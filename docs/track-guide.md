# Track Guide

This guide helps you pick a {term}`track` from the genomic data type you have
and shows how each family behaves. It teaches the canonical, compatibility-
preferred name for every concept and flags the retained aliases. Exact
signatures, inherited fields, defaults, accepted literals, and alias fields
are generated per class in the {doc}`api/tracks` and are not repeated here.

All tracks share the base {class}`pygv.tracks.Track` configuration — name,
height, colors, alpha, fonts, y-axis labels, and {term}`track highlight`
helpers — and every track renders over the same zero-based, half-open
{term}`genomic interval`. A track receives the interval at plot time; see
{doc}`data-formats` for sources, indexing, and validation.

## Choosing a track by data type

| Data type | Canonical track | Notes |
|---|---|---|
| Gene or interval annotation (BED) | {class}`pygv.tracks.BedTrack` | BED3/4/6/8/12; {term}`feature lane` placement |
| Gene annotation (GTF) | {class}`pygv.tracks.GtfTrack` | Transcript and exon structure |
| BigBed intervals | {class}`pygv.tracks.BigBed6Track` | Self-indexed, local or remote |
| Mutation lollipops | {class}`pygv.tracks.UCSCMutationTrack` | UCSC-style mutational bigBed |
| Read coverage (BAM) | {class}`pygv.tracks.CoverageTrack` | Aggregate numerical coverage |
| Stranded coverage (BAM) | {class}`pygv.tracks.StrandSpecificCoverageTrack` | Positive and negative channels |
| Individual reads (BAM) | {class}`pygv.tracks.CollapsedReadTrack` | 5' end and span |
| Spliced reads (BAM) | {class}`pygv.tracks.SplicedReadTrack` | Exon blocks and junctions |
| Read junctions as arcs | {class}`pygv.tracks.ReadArcTrack` | Arc rendering of read spans |
| Continuous signal (BigWig) | {class}`pygv.tracks.BigWigTrack` | One or more sources, line or bar |
| Values supplied in code | {class}`pygv.tracks.DynamicValueTrack` | No backing file required |
| Several signals overlaid | {class}`pygv.tracks.OverlayingTrack` | Labelled overlay |
| Stranded signal pair | {class}`pygv.tracks.PairedStrandSpecificTrack` | Separate positive/negative channels |
| Strand-collapsed pair | {class}`pygv.tracks.PairedStrandlessTrack` | Summed into one signal |
| Two scales on one axis | {class}`pygv.tracks.DualAxisTrack` | {term}`dual-axis track` |
| Paired anchors (BEDPE) | {class}`pygv.tracks.BedPETrack` | {term}`BEDPE link <bedpe link>` rendering |
| Directional connections | {class}`pygv.tracks.ConnectionArcTrack` | Source-to-target arcs |
| Sequence logo | {class}`pygv.tracks.LogoTrack` | Matrix assigned through `values` |
| Signal plus sequence | {class}`pygv.tracks.DynseqTrack` | BigWig heights with FASTA context |
| Association results | {class}`pygv.tracks.GWASTrack` | {term}`GWAS marker <gwas marker>` from BED6+ |

## Annotation tracks

Annotation tracks draw discrete features. They share the base
{class}`pygv.tracks.AnnotationTrack` behavior, including {term}`feature lane`
placement so overlapping features do not obscure one another. `show_mode`
selects `expanded` (overlapping features stay in separate lanes) or
`collapsed` (overlaps share a lane); any other value fails validation.

- {class}`pygv.tracks.BedTrack` renders BED-style intervals. Optional BED
  columns enrich blocks, thickness, labels, strand arrows, and item colors
  without changing interval selection. Missing optional fields degrade to
  simpler rendering rather than failing.
- {class}`pygv.tracks.GtfTrack` renders transcript and gene structures and
  associates exon blocks with their parent transcripts. An optional `filters`
  callable runs before plotting, `show_genes` controls gene-level display,
  `show_transcript_id` controls transcript labels, and `annotation_formatter`
  formats the displayed name.
- {class}`pygv.tracks.BigBed6Track` accepts local or remote BigBed sources,
  normalizes records to BED6-compatible fields, sorts them for deterministic
  rendering, and exposes `get_filters()` / `set_filters(key, value)`.
- {class}`pygv.tracks.UCSCMutationTrack` renders mutation lollipops with the
  same filter methods, plus optional highlighting and a color gradient.

## Alignment tracks

Alignment tracks read a BAM source that has a readable index. Optional
`filters` callables select reads before rendering, and sampling reduces detail
without moving genomic coordinates. A missing index or an unsupported coloring
mode fails explicitly.

- {class}`pygv.tracks.CoverageTrack` and
  {class}`pygv.tracks.StrandSpecificCoverageTrack` render aggregate numerical
  coverage; the strand-specific variant draws positive and negative channels
  distinctly.
- {class}`pygv.tracks.CollapsedReadTrack` draws each read's 5' end and span,
  and {class}`pygv.tracks.SplicedReadTrack` draws exon blocks and junctions.
  Both can color reads by a supported criterion.
- {class}`pygv.tracks.ReadArcTrack` draws reads or junctions as arcs, with
  distinct start and end colors.

## Numerical signal tracks

Numerical tracks share {class}`pygv.tracks.NumericalTrack`: range controls
(`min_val`, `max_val`), optional binning (`n_bins` with `stat_method`),
`data_transform`, NaN handling (`convert_nan_to_num`), `scale`, and overflow
labels. `reset_min_val()` and `reset_max_val()` restore automatic bounds.

- {class}`pygv.tracks.BigWigTrack` reads one or more local or remote BigWig
  sources and renders them with `plot_type` `"line"` or `"bar"`.
- {class}`pygv.tracks.DynamicValueTrack` takes its values from code instead of
  a file, which is useful for computed tracks and tests.
- {term}`Group autoscale` gives selected numerical tracks the same rendered
  y-axis range and ticks; register it through the {term}`genome viewer` rather
  than per track.

Named `data_transform` strings are `asinh`, `ln`, `log2`, `log10`, and
`log1p`, plus `r`-prefixed variants (`rln`, `rlog2`, `rlog10`, `rlog1p`) for
the negative axis. A callable is also accepted. `stat_method` accepts `mean`,
`std`, `median`, `count`, `sum`, `min`, or `max`.

## Paired and overlay compositions

These tracks combine several signals in one subplot:

- {class}`pygv.tracks.OverlayingTrack` overlays one or more labeled sources and
  preserves source order, labels, and colors.
- {class}`pygv.tracks.PairedStrandSpecificTrack` is the **canonical** name for
  rendering a positive and a negative strand channel with distinct colors and
  a shared, zero-centred range.
- {class}`pygv.tracks.PairedStrandSpecificTracks` is a **retained compatibility
  alias** of the canonical paired track. It has the same fields and behavior;
  prefer the singular name in new code.
- {class}`pygv.tracks.PairedStrandlessTrack` combines a positive and negative
  source into one strand-collapsed signal.
- {class}`pygv.tracks.DualAxisTrack` composes two existing tracks into one
  {term}`dual-axis track` with independent left and right y-axes, forwarding
  preparation, drawing, and highlights to both children.

## Connections

Connection tracks render relationships between genomic anchors:

- {class}`pygv.tracks.BedPETrack` renders paired anchors from BEDPE input and
  supports exact link highlighting through `set_highlight_links(links)`,
  `add_highlight_link(link)`, and `clear_highlight_links()`.
- {class}`pygv.tracks.ConnectionArcTrack` renders directional connections from
  BED-compatible records, with a configurable Matplotlib arrow style and an
  optional connection style or arc radius.

## Sequence tracks

- {class}`pygv.tracks.LogoTrack` renders a sequence-logo matrix assigned
  through its `values` property. The matrix length must equal the plotted
  interval span; a mismatch raises `ValueError`. A NumPy input is normalized to
  a DataFrame with nucleotide columns when applicable.
- {class}`pygv.tracks.DynseqTrack` combines BigWig letter-height signal with
  local FASTA sequence context.

## GWAS

{class}`pygv.tracks.GWASTrack` renders SNP-oriented association results from a
local BED6+ source. The documented contract is:

- **Raw p-values.** BED column 5 (`score`) is the *raw* p-value, not a
  transformed score. Columns after BED6 are ignored.
- **Unit-width records.** Every accepted record represents a single base:
  `end - start == 1`. Rows that are not unit width are rejected.
- **Interval selection.** Only records whose start lies in the plotted
  half-open interval are rendered.
- **Y transform.** `y_transform` defaults to `-log10(p)`. It accepts a callable
  over either the p-value vector or individual p-values; the result must be
  finite and shape-aligned, or it raises `ValueError`.
- **Zero-value warning.** A p-value of exactly `0` cannot be log-transformed.
  Zero-valued rows are skipped with at most one `RuntimeWarning` per track
  instance.
- **Significance lines.** `significance_lines` holds *raw* p-values. They pass
  through the same transform and are drawn with defaults that
  `significance_line_kws` can override. An empty interval still renders the
  configured significance lines, and thresholds outside `(0, 1]` raise
  `ValueError`.
- **Validation.** A record must have at least six fields, numeric
  start/end/score values, unit width, and a p-value in `(0, 1]`. Records that
  violate these rules raise `ValueError` on every reader path.
- **Sources.** Local BED6+ files are read through pandas. A `.gz` source with
  a `.tbi` index uses interval-aware Tabix access. Remote sources are not
  accepted.

```{admonition} Known issue: indexed GWAS reader
:class: warning

The indexed (bgzipped + Tabix) reader has a tracked defect: it can return an
empty result instead of raising when an indexed record is malformed. That is a
bug against the contract above, not supported behavior, and it is tracked separately.
The documented contract stands unchanged: malformed records must
fail, and a merely absent contig may render empty. This issue does not change
the contract for other tracks or block work on unrelated pages.```

## Compatibility aliases

PyGV prefers singular, descriptive field names. The following names are
canonical; the alias is retained for compatibility and accepted at
construction time only (it is not accepted on later attribute assignment):

| Canonical field | Retained alias |
|---|---|
| `inward_yticks` | `inward_ticks` |
| `data_transform` | `transformation` |
| `equal_space_for_pos_neg_ranges` | `draw_y_independently` |
| `flip_arc` | `flip` |

Use the canonical name in new code. The generated {doc}`api/tracks` marks the
alias next to each affected field.

## Extension seams

A track exposes exactly three underscore-prefixed lifecycle seams for
extensions; the {term}`genome viewer` calls them in this order for every
registered track:

- `_pre_plot_hook(chromosome, start, end, **kwargs)` prepares interval-specific
  state before axes are created.
- `_draw_track(chromosome, start, end, ax, index=1, **kwargs)` binds and draws
  on the viewer-provided axis.
- `_post_plot_hook(chromosome, start, end, ax, index=1, **kwargs)` applies
  highlights and final axis behavior.

These hooks must be safe for repeated plots of different intervals on the same
object. Any other underscore-prefixed member is an implementation detail and is
not part of the documented surface.
