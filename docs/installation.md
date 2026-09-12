# Installation and quickstart

## Install

Install the distribution from PyPI:

```shell
pip install GenomeViewer
```

The distribution is named **`GenomeViewer`**, but the import namespace is
**`pygv`**. If you search your environment for the wrong name you will not
find it:

```python
import pygv          # correct
from pygv.viewer import GenomeViewer
```

PyGV requires Python 3.10 or newer and installs its numerical and genomics
dependencies (NumPy, Matplotlib, pandas, SciPy, pysam, pyBigWig, pyfaidx, and
Pydantic) automatically. The exact supported versions are those declared by
the paired code commit recorded in {doc}`provenance`.

## Quickstart

The following program creates a {term}`genome viewer`, adds one annotation
track from a small BED file, plots a {term}`genomic interval`, and saves the
figure. It is executed by the documentation test suite, so the published
snippet is guaranteed to run.

```{literalinclude} _examples/quickstart.py
:language: python
:start-after: [start:quickstart]
:end-before: [end:quickstart]
:dedent:
```

The interval `("chr1", 0, 100)` is zero-based and half-open: it includes
position 0 and excludes position 100.

`gv.plot(...)` returns the Matplotlib axes that PyGV drew on. The figure itself
is the current Matplotlib figure, so you can keep customizing it with
`matplotlib.pyplot` before saving. See the API reference for the full
{term}`genome viewer` surface.
