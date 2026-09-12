# PyGV documentation

**PyGV** (the *Python Genome Viewer*) is a Python package for building
publication-ready genome browser figures. You compose a {term}`genome viewer`
from one or more {term}`track` objects over a single {term}`genomic interval`,
then render, inspect, or save the resulting Matplotlib figure.

```{admonition} Documentation channel
:class: note

This is the **{{ doc_channel }}** documentation channel. It was built from
documentation commit {{ doc_commit_short }} and describes the public code
commit {{ code_commit_short }} on the {{ code_branch }} branch. See
{doc}`provenance` for the full pairing.
```

```{toctree}
:hidden:
:maxdepth: 2

overview
installation
concepts
api/index
provenance
```

## Where to start

- {doc}`overview` explains what PyGV does and how its pieces fit together.
- {doc}`installation` installs the package and renders a first figure.
- {doc}`concepts` defines the vocabulary for composing a genome viewer.
- {doc}`api/index` is the generated reference for the public API.
- {doc}`provenance` records exactly which revisions this site describes.
