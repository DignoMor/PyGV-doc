# Core Concepts

**PyGV** composes heterogeneous genomic data into vertically aligned visual
{term}`track`\ s over one {term}`genomic interval`. This page defines the pieces
you compose with; the {doc}`api/index` gives the exact signatures and defaults
from the pinned code revision.

## Genome viewers

A {term}`genome viewer` is an ordered composition of tracks that share one
genomic interval and render as one figure. In code it is a `GenomeViewer`. The
viewer owns track order, figure layout, shared annotations (highlights, lines,
and marks), and the render lifecycle. It stays independent of track file
formats: a concrete track owns its source validation, interval retrieval, and
rendering.

## Tracks

A {term}`track` is one vertically allocated view of genomic data or annotation
within a genome viewer. Two broad kinds appear throughout PyGV:

- An {term}`annotation track` draws discrete genomic features such as genes,
  intervals, or links.
- A {term}`numerical track` draws measurements positioned along genomic
  coordinates.

Annotation tracks place overlapping features into {term}`feature lane`\ s so the
features do not obscure one another. A {term}`dual-axis track` is a composition
that draws two child tracks against independent left and right y-axes over the
same interval.

## Track sources

A {term}`track source` is the file, URL, or in-memory values from which a track
obtains its genomic data. A track can read a local file, a remote file, an
indexed file, or values you supply directly. The source is a separate concern
from the track that renders it, and source validation happens when a track is
prepared for plotting rather than when the viewer is created.

## Genomic intervals and coordinates

PyGV describes genomic coordinates as **zero-based** and **half-open**, matching
BED. A {term}`genomic interval` is a chromosome or contig together with a range
`[start, end)`: it includes `start` and excludes `end`. A single-base feature at
the first base of a chromosome is `start=0, end=1`. The viewer hands the same
zero-based, half-open interval to every track during `plot`. Prefer "interval"
over "region" or "window" when the coordinate convention matters.

## Ordering and layout

Tracks render in registration order: the first track you add is drawn at the
top. `add_track` and `add_tracks` append a track to the registration order, and
`remove_track` removes one. `show_tracks` reports the registered tracks as
`(name, type, object)` tuples in that order.

Each track reports a layout height, and the figure height is the sum of those
heights scaled by `height_scale_factor`, unless you pass an explicit
`fig_height`. The `hspace` constructor argument reserves vertical space between
tracks as a fraction of the average axis height. Rendering produces one
Matplotlib axis per registered track.

## Rendering

`plot(chromosome, start, end, ...)` is the render lifecycle. It validates the
registered tracks, prepares them for the interval, creates the figure and axes,
draws every track in registration order, then adjusts layout and adds shared
annotations. All tracks receive the same zero-based, half-open interval.
Plotting with no tracks raises `RuntimeError`.

`plot` returns a Python list of Matplotlib axes, one per track. The figure is the
current Matplotlib figure, so you can keep customizing it with the Matplotlib
API after PyGV has drawn the tracks. `save` delegates to
`matplotlib.pyplot.savefig` and, for PDF output, adds PyGV/genomic metadata plus
a tight bounding box. You can inspect registration with `show_tracks`, display
the figure with `matplotlib.pyplot.show`, and write it to disk with `save`.

## Group autoscale and group labels

These are distinct concepts that happen to span more than one track.

A {term}`group autoscale` gives selected numerical tracks the same rendered
y-axis range and ticks. Register a group by track index with
`add_group_autoscale` or by track name with `add_group_autoscale_by_name`;
`reset_group_autoscale` clears every rule. Autoscaling copies the range, ticks,
labels, and functional scale of the grouped track with the widest rendered
y-span. Unknown names, invalid indexes, and non-numerical tracks produce runtime
warnings.

A {term}`group label` is a label spanning a contiguous vertical range of
tracks. Add one by index range with `add_group_label` or by start and end track
names with `add_group_label_by_name`. Autoscale changes the numbers shown on
axes; a group label only names a vertical range of tracks.

## Highlights, lines, and marks

Track-level and figure-wide annotations are separate concepts.

- A {term}`track highlight` is a genomic span drawn within the axes of selected
  tracks. `set_highlight_regions` applies one or more highlight regions to every
  registered track, using the chromosome supplied to `plot`, and requires
  tracks to be registered first. To highlight only specific tracks, call a
  track's own highlight method instead.
- A {term}`global highlight` is a genomic span drawn continuously across tracks
  and the spaces between them. `set_global_highlight_region` adds it after
  plotting; partial overlaps are clipped to the plotted interval, and a span
  entirely outside that interval produces a warning.
- An {term}`axis mark` is a position marker attached to the top coordinate axis
  of the first track, optionally carrying a label. `set_axis_marks` adds marks
  after plotting; when labels are supplied they must match the number of
  positions, and out-of-range positions are omitted.
- A {term}`global vertical line` is a positional line drawn across every track
  and the spaces between them. `set_global_vertical_line` adds it after plotting
  and warns when the position lies outside the plotted interval.

Global highlights, global vertical lines, and axis marks all require a completed
`plot` call; before that they raise `RuntimeError`.
