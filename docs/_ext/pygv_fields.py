"""Render Pydantic track configuration from the pinned checkout.

Autodoc alone renders a track model's generated constructor signature but not
the Pydantic ``Field`` descriptions, compatibility aliases, or the fact that a
field was inherited. This extension derives a configuration summary from each
model's ``model_fields`` at build time and rewrites the constructor signature
with the public type aliases, so the reference always describes the pinned
code revision instead of a hand-maintained matrix.

Only classes that are instances of ``pydantic.BaseModel`` are touched. A
class docstring gets a definition list of its fields (inherited fields
included); a class signature gets friendly type names such as ``Color`` and
``Alpha`` in place of ``Annotated[...]`` reprs. No code checkout is modified.
"""

from __future__ import annotations

import inspect
import typing
from typing import Any

try:  # pragma: no cover - exercised only at documentation build time
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = None

_TYPE_ALIASES = {
    "_validate_color": "Color",
    "_validate_color_sequence": "ColorSequence",
    "_validate_filter": "FilterFn",
}

_SIMPLE_ORIGINS = {
    list: "List",
    tuple: "Tuple",
    dict: "Dict",
    set: "Set",
    frozenset: "FrozenSet",
}


def _validator_alias(metadata: tuple) -> str | None:
    for item in metadata:
        func = getattr(item, "func", None)
        name = getattr(func, "__name__", None)
        if name in _TYPE_ALIASES:
            return _TYPE_ALIASES[name]
    return None


def _render_type(annotation: Any) -> str:
    if annotation is None or annotation is inspect.Parameter.empty:
        return "Any"
    if isinstance(annotation, str):
        return annotation

    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        args = typing.get_args(annotation)
        base, metadata = args[0], args[1:]
        alias = _validator_alias(metadata)
        if alias:
            return alias
        constraint_names = {type(item).__name__ for item in metadata}
        if constraint_names == {"Gt"}:
            return "PositiveFloat"
        if "Ge" in constraint_names and "Le" in constraint_names:
            return "Alpha"
        return _render_type(base)

    if origin is typing.Literal:
        values = ", ".join(repr(arg) for arg in typing.get_args(annotation))
        return f"Literal[{values}]"

    if origin is typing.Union:
        args = typing.get_args(annotation)
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return f"Optional[{_render_type(non_none[0])}]"
        rendered = ", ".join(_render_type(arg) for arg in args)
        return f"Union[{rendered}]"

    if origin is not None:
        args = typing.get_args(annotation)
        base_name = _SIMPLE_ORIGINS.get(origin)
        if base_name is None:
            base_name = getattr(origin, "__name__", str(origin))
        if args:
            rendered = ", ".join(_render_type(arg) for arg in args)
            return f"{base_name}[{rendered}]"
        return base_name

    if annotation is Any:
        return "Any"
    if annotation is type(None):
        return "None"
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation)


def _render_default(default: Any) -> str:
    if type(default).__name__ == "_HAS_DEFAULT_FACTORY_CLASS":
        return "<factory>"
    if default is None:
        return "None"
    if isinstance(default, bool):
        return repr(default)
    if callable(default) and getattr(default, "__name__", None):
        return default.__name__
    return repr(default)


def _friendly_signature(obj: Any) -> str | None:
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return None

    parts: list[str] = []
    emitted_star = False
    for name, parameter in signature.parameters.items():
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            parts.append(f"*{name}")
            emitted_star = True
            continue
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY and not emitted_star:
            parts.append("*")
            emitted_star = True

        annotation = _render_type(parameter.annotation)
        label = f"{name}: {annotation}" if annotation else name
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            parts.append(f"**{name}: {annotation}" if annotation else f"**{name}")
            continue
        if parameter.default is inspect.Parameter.empty:
            parts.append(label)
        else:
            parts.append(f"{label} = {_render_default(parameter.default)}")

    rendered = f"({', '.join(parts)})"
    return rendered + " -> None"


def _field_listing(obj: Any) -> list[str]:
    fields = getattr(obj, "model_fields", None)
    if not fields:
        return []

    lines = ["", "**Configuration fields**", ""]
    for name, field in fields.items():
        annotation = _render_type(field.annotation)
        if field.is_required():
            default = "required"
        elif field.default_factory is not None:
            default = "<factory>"
        else:
            default = _render_default(field.get_default(call_default_factory=False))
        description = (field.description or "").strip()

        summary = f"``{annotation}``"
        summary += " required" if default == "required" else f", default ``{default}``"
        if description:
            summary += f". {description}"
        aliases = []
        candidate = field.validation_alias
        if isinstance(candidate, str):
            aliases.append(candidate)
        elif candidate is not None:
            for choice in getattr(candidate, "choices", ()):
                if isinstance(choice, str):
                    aliases.append(choice)
        aliases = [alias for alias in aliases if alias != name]
        if aliases:
            joined = ", ".join(f"``{alias}``" for alias in aliases)
            summary += f" Alias: {joined}."

        lines.append(f"``{name}``")
        lines.append(f"    {summary}")
        lines.append("")
    return lines


def _process_signature(app, what, name, obj, options, signature, return_annotation):
    if what != "class" or BaseModel is None:
        return signature, return_annotation
    if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
        return signature, return_annotation
    friendly = _friendly_signature(obj)
    if friendly is None:
        return signature, return_annotation
    return friendly, ""


def _process_docstring(app, what, name, obj, options, lines):
    if what != "class" or BaseModel is None:
        return
    if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
        return
    lines.extend(_field_listing(obj))


_FIELD_NAMES: set[str] | None = None


def _track_field_names() -> set[str]:
    """Union of every exported track model's field names.

    Pydantic exposes model fields as class members, and autodoc would render
    each as a bare attribute with the raw ``Annotated[...]`` repr. The
    configuration summary above documents them instead, so these member
    entries are skipped.
    """
    global _FIELD_NAMES
    if _FIELD_NAMES is not None:
        return _FIELD_NAMES
    names: set[str] = set()
    try:
        import pygv.tracks as tracks

        for export in getattr(tracks, "__all__", ()):
            model = getattr(tracks, export, None)
            names.update(getattr(model, "model_fields", {}) or {})
    except Exception:  # pragma: no cover - checkout always importable at build
        pass
    _FIELD_NAMES = names
    return names


def _skip_member(app, what, name, obj, skip, options):
    if what == "class" and name in _track_field_names():
        return True
    return None


def setup(app):
    app.connect("autodoc-process-signature", _process_signature)
    app.connect("autodoc-process-docstring", _process_docstring)
    app.connect("autodoc-skip-member", _skip_member)
    return {"version": "1.0", "parallel_read_safe": True}
