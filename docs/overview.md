# Overview

PyGV builds genome browser figures in Python. A figure is a stack of
{term}`track`\ s laid out over one {term}`genomic interval`; each track reads a
data file or values you supply, and Matplotlib renders the result. Because the
output is an ordinary Matplotlib figure, you can keep styling it with the
Matplotlib API after PyGV has drawn the tracks.

PyGV is designed for figures that need to be reproducible: tracks are Python
objects with typed configuration fields, so a figure can be described in code,
reviewed, and regenerated.

## The distribution and the import name

PyGV is distributed on PyPI as **`GenomeViewer`**, but the Python package you
import is **`pygv`**:

```shell
pip install GenomeViewer
```

```python
from pygv.viewer import GenomeViewer
from pygv.tracks import GtfTrack
```

The two names are not interchangeable. Install `GenomeViewer` and import
`pygv`.

## How a figure is assembled

1. Create a {term}`genome viewer`.
2. Add one or more {term}`track`\ s, each with its own data source.
3. Call the viewer's plot method over a {term}`genomic interval`.
4. Show or save the resulting Matplotlib figure.

{doc}`installation` walks through this sequence with a runnable example. The
API reference derives every signature and default from the paired code commit
recorded in {doc}`provenance`.

## Coordinate conventions

PyGV describes genomic coordinates the same way BED does: a {term}`genomic
interval` is **zero-based** and **half-open**. The interval `(start, end)`
includes `start` and excludes `end`. A single-base feature at the first base of
a chromosome is `start=0, end=1`.

## Canonical terms

```{glossary}
genome viewer
    A PyGV object that owns a set of tracks, their vertical layout, and the
    Matplotlib axes they are drawn on. Its public type is
    {class}`pygv.viewer.GenomeViewer`.

track
    A visual layer in a genome viewer that reads one data source and draws it
    over the plotted interval. Tracks are Python objects.

track source
    The data a track reads: a local file, a remote file, an indexed file, or
    in-memory values supplied by the caller.

genomic interval
    A zero-based, half-open range of a reference sequence, written as a
    chromosome together with a start and an end coordinate.

annotation track
    A track that draws named features such as genes or regulatory elements.

numerical track
    A track that draws a numeric signal as a line or bar over the interval.
```
