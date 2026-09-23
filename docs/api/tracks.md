# Track API reference

The 24 classes exported by `pygv.tracks` are documented here. Every constructor
signature, inherited configuration field, default, accepted literal, and
compatibility alias is generated from the pinned code revision described in
{doc}`../provenance`; nothing on this page is hand-copied. The
{doc}`../track-guide` explains which track to use for a data type, and
{doc}`../data-formats` covers source, indexing, and coordinate expectations.

```{admonition} Configuration fields
:class: note

Each class lists its own and inherited Pydantic configuration fields, with the
field description, default (or `required`), accepted literal values, and any
retained compatibility alias. Prefer the canonical field name; aliases are
accepted for compatibility only.
```

Only the three contracted lifecycle seams — `_pre_plot_hook`, `_draw_track`,
and `_post_plot_hook` — are part of the public extension surface. Other
underscore-prefixed helpers are implementation details and are not documented.
The base hooks are described in {doc}`../track-guide`.

## Base tracks

`Track` is the root of every model. `AnnotationTrack` adds discrete-feature and
{term}`feature lane` behavior, `NumericalTrack` adds coordinate/value
rendering, `DynamicValueTrack` supplies numerical values from code, and
`DualAxisTrack` composes a left and right child track into one
{term}`dual-axis track`.

```{eval-rst}
.. autoclass:: pygv.tracks.Track
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.AnnotationTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.NumericalTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.DynamicValueTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.DualAxisTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## Alignment tracks

Alignment tracks read an indexed BAM source. Coverage and strand-specific
coverage render numerical signal; collapsed, spliced, and arc tracks render
read-level glyphs.

```{eval-rst}
.. autoclass:: pygv.tracks.CoverageTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.StrandSpecificCoverageTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.CollapsedReadTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.SplicedReadTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.ReadArcTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## Interval and connection tracks

`BedTrack` renders BED interval features, `BedPETrack` renders paired
{term}`BEDPE link` anchors, and `ConnectionArcTrack` renders directional
connections between BED-compatible anchors.

```{eval-rst}
.. autoclass:: pygv.tracks.BedTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.BedPETrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.ConnectionArcTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## BigBed tracks

BigBed sources are self-indexed and support local or remote input.
`BigBed6Track` normalizes records to BED6, and `UCSCMutationTrack` renders
mutation lollipops with optional filtering and a color gradient.

```{eval-rst}
.. autoclass:: pygv.tracks.BigBed6Track
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.UCSCMutationTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## BigWig signal tracks

`BigWigTrack` renders one or more numerical sources as a line or bar.
`OverlayingTrack` overlays several labeled signals, the paired tracks separate
positive and negative strands, and `PairedStrandlessTrack` collapses a pair
into one signal. `PairedStrandSpecificTrack` is the canonical paired name;
`PairedStrandSpecificTracks` is a retained compatibility alias.

```{eval-rst}
.. autoclass:: pygv.tracks.BigWigTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.OverlayingTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.PairedStrandSpecificTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.PairedStrandSpecificTracks
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.PairedStrandlessTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## Gene annotation track

`GtfTrack` renders transcript and gene structures from GTF, associating exon
blocks with parent transcripts.

```{eval-rst}
.. autoclass:: pygv.tracks.GtfTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## GWAS track

`GWASTrack` renders single-base association records from a local BED6+ source.
See {doc}`../track-guide` for the raw-p-value, unit-width record, y-transform,
zero-value, and significance-line contract.

```{eval-rst}
.. autoclass:: pygv.tracks.GWASTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

## Sequence tracks

`LogoTrack` renders an assigned sequence-logo matrix, and `DynseqTrack`
combines a BigWig signal with local FASTA sequence context.

```{eval-rst}
.. autoclass:: pygv.tracks.LogoTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```

```{eval-rst}
.. autoclass:: pygv.tracks.DynseqTrack
   :members:
   :inherited-members:
   :private-members: _pre_plot_hook, _draw_track, _post_plot_hook
   :exclude-members: model_config, model_fields, model_fields_set, model_computed_fields, model_extra, model_dump, model_dump_json, model_validate, model_validate_json, model_validate_strings, model_construct, model_copy, model_rebuild, model_json_schema, model_parametrized_name, model_post_init, copy, dict, json, parse_file, parse_obj, parse_raw, schema, schema_json, construct, from_orm, update_forward_refs, validate
```
