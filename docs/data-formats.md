# Data Formats and Coordinates

A {term}`track source` is the file, URL, or in-memory values a track reads. A
concrete track owns its source validation, interval retrieval, and rendering,
so the {term}`genome viewer` stays independent of file formats. This page
describes the supported source formats, how local and remote inputs differ,
which sources need an index, the coordinate convention, and what validation to
expect. For per-class fields see the {doc}`api/tracks`; for choosing a track
see the {doc}`track-guide`.

## Genomic-coordinate conventions

PyGV describes a {term}`genomic interval` the way BED does: **zero-based** and
**half-open**. The interval `(start, end)` includes `start` and excludes `end`.
A single-base feature at the first base of a chromosome is `start=0, end=1`.
The viewer hands the same zero-based, half-open interval to every track during
`plot`, and interval-aware readers query with those bounds directly.

Two practical consequences follow:

- A feature that abuts the end of the plotted interval is not drawn when its
  start equals `end`; it lies outside the interval.
- GWAS records are single-base {term}`GWAS marker <gwas marker>`\ s, so an accepted unit-width
  record has `end - start == 1` and its `start` selects the interval.

Chromosome names are used exactly as they appear in the source; PyGV does not
translate between `chr1` and `1`.

## Source formats

| Family | Typical format | Reader |
|---|---|---|
| Interval annotation | BED3/4/6/8/12 | pandas for plain text; Tabix for bgzipped indexed files |
| Gene annotation | GTF | pandas for plain text; `pysam` for bgzipped indexed files |
| Paired anchors | BEDPE | pandas for plain text; interval-aware access for indexed files |
| BigBed | `.bb` / `.bigBed` | `pyBigWig`-style indexed access |
| Signal | BigWig | `pyBigWig` |
| Alignment | BAM | `pysam` |
| Sequence | FASTA | `pyfaidx` |
| Association results | BED6+ | pandas, or `pysam` Tabix for `.gz` + `.tbi` |

BED files may omit optional columns; missing optional fields degrade to
simpler rendering. BigBed input is normalized to BED6-compatible fields, and
extra fields are truncated with a warning where BED6 normalization applies.
Input that is not the expected format fails explicitly rather than being
silently ignored.

## Local and remote inputs

BigWig and BigBed tracks accept local paths and remote URLs; BED, GTF, BEDPE,
BAM, FASTA, and GWAS sources are local. GWAS specifically does not accept
remote sources.

Source accessibility is validated by `check_accessibility`. It returns `True`
when a local path exists and, only when `allow_remote=True`, also treats
strings beginning with `http` or `ftp` as accessible. It does **not** probe a
remote endpoint over the network and does not validate file contents; a remote
string is accepted by prefix alone. Inaccessible locations raise `ValueError`
unless the caller passes `raise_except=False`.

## Indexing expectations

Indexed access is interval-aware; without an index a track must load and
filter the whole source, which is slower and may not be supported.

- **BAM** requires a readable index (for example a `.bai` alongside the BAM).
  A missing index fails explicitly.
- **BigWig and BigBed** are self-indexed formats; no separate index file is
  needed.
- **bgzipped BED / GTF / BEDPE** use interval-aware access when the matching
  index (for example `.tbi`) is present; uncompressed sources use the pandas
  parser instead.
- **GWAS** uses interval-aware Tabix access only for a `.gz` source that has a
  `.tbi` index. Other local GWAS sources are loaded through pandas and filtered
  to the requested interval.

## Validation behavior

Track configuration is validated by Pydantic v2. Validation is deliberate and
happens at construction and on assignment:

- **Unknown keys are rejected.** Track models forbid extra configuration keys,
  so a misspelled keyword raises a validation error instead of being ignored.
- **Values are type-checked.** Colors must be Matplotlib-compatible, `alpha`
  is bounded to `[0, 1]`, and `height` must be positive. Invalid filters and
  invalid `stat_method` values raise a validation error.
- **Literals are enforced.** `show_mode` accepts `expanded` or `collapsed`;
  `plot_type` accepts `line` or `bar`; `stack_order` accepts `big_on_top`,
  `small_on_top`, or `fixed`; `color_reads_by` accepts only its documented
  values.
- **Aliases work at construction only.** Compatibility aliases such as
  `inward_ticks` resolve during initialization, not on later attribute
  assignment. Prefer canonical names.
- **Sources fail early or explicitly.** Inaccessible sources fail during
  initialization for tracks that open them then, and index or coloring-mode
  problems fail explicitly rather than rendering something misleading.
- **Intervals can be empty.** An empty interval renders without a hard failure
  where the data format allows it.

See {doc}`track-guide` for the GWAS-specific validation rules, including
unit-width records, raw p-values, zero-value handling, and significance lines.
