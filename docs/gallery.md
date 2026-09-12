# Complete Gallery

The **Complete Gallery** collects every public example owned by the PyGV code
repository. Each example is generated and executed during the documentation
build from the exact pinned code checkout that produces the {doc}`API reference
<api/index>`, so the rendered figures, source listings, and downloads all
describe the same code revision.

Examples are never copied into this repository. Their scripts and fixtures stay
owned by the code repository and are read from the paired checkout at build
time; the generated gallery pages are disposable build output. Before reusing a
figure, review the {doc}`third-party notices <third-party-notices>` for the
example data and asset terms.

```{note}
Gallery cache identity: the build writes the gallery under
`gallery/<channel>/<code-revision>-<dependency-lock>` and re-executes every
example when either the pinned code revision or `requirements.txt` changes.
```

```{toctree}
:glob:
:maxdepth: 1

gallery/*/*/index
third-party-notices
```
