# PyGV documentation

**PyGV** (the *Python Genome Viewer*) is a Python package for building
publication-ready genome browser figures. You compose a {term}`genome viewer`
from one or more {term}`track` objects over a single {term}`genomic interval`,
then render, inspect, or save the resulting Matplotlib figure.

```{admonition} Documented software
:class: note

**PyGV {{ release }}** · **{{ doc_channel }}** documentation channel.

- Code repository: {{ code_repository_link }} — {{ code_commit_link }}
  on `{{ code_branch }}`.
- Documentation repository: {{ doc_repository_link }} — {{ doc_commit_link }}.

See {doc}`provenance` for the full pairing.
```

```{toctree}
:hidden:
:maxdepth: 2

overview
installation
concepts
track-guide
api/index
data-formats
gallery
changelog
provenance
```

## Where to start

- {doc}`overview` explains what PyGV does and how its pieces fit together.
- {doc}`installation` installs the package and renders a first figure.
- {doc}`concepts` defines the vocabulary for composing a genome viewer.
- {doc}`track-guide` helps you choose a track by genomic data type.
- {doc}`api/index` is the generated reference for the public API.
- {doc}`data-formats` documents sources, indexing, and coordinates.
- {doc}`gallery` executes and renders every public example.
- {doc}`changelog` summarizes the paired revision's compatibility changes.
- {doc}`provenance` records exactly which revisions this site describes.
