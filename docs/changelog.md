# Changelog and Migration

This page summarizes the public compatibility changes for the code revision
paired with this documentation site, as recorded in the
{doc}`paired code repository <provenance>`. It focuses on changes that affect
how you write PyGV code; it is not a release ledger.

## Compatibility changes

### Breaking

- **Python 3.10+ is required.** The package no longer supports older
  interpreters.
- **Unknown track keyword arguments raise an error.** Track models forbid
  extra keys, so a typo that older versions ignored now raises a validation
  error. Remove or correct any extra keywords.
- **Track layout height is `layout_height()`.** Annotation and dual-axis
  layout height comes from `layout_height()`, not from `.height`. The `.height`
  field remains the per-lane unit that the {term}`genome viewer` scales through
  `layout_height()`. Replace code that read `.height` to size a figure.
- **Extra positional arguments were removed.**
  `BigWigTrack(path, "bar")` and an `OverlayingTrack(..., palette)` positional
  argument are no longer accepted. Pass `plot_type=` and `palette=` as keyword
  arguments instead.
- **Constructor aliases apply at initialization only.** Aliases such as
  `inward_ticks`, `transformation`, and `draw_y_independently` work when the
  track is constructed, but not on later attribute assignment. Prefer the
  canonical names (`inward_yticks`, `data_transform`,
  `equal_space_for_pos_neg_ranges`).
- **Invalid configuration raises instead of being ignored.** Invalid colors,
  filters, and `stat_method` values now raise a validation error rather than
  silently falling back.
- **File handles are private.** Attributes such as `_bam` and `_bw` are
  implementation details; do not depend on them.

### Fixed

- **Uncompressed GTF and BEDPE parsing.** Uncompressed `.gtf` / `.bedpe`
  files are no longer opened with Tabix when `pysam` is installed; `GtfTrack`
  has a pandas fallback parser.
- **Sequence-logo values are preserved.** `LogoTrack.values` keeps the
  A/C/G/T (or amino-acid) DataFrame when given a NumPy array.
- **Track highlight defaults.** `add_highlight_region` records the default
  color and alpha so highlights are drawn.
- **Coverage transforms.** Coverage tracks apply `data_transform` and `scale`.
- **GTF layout height.** `GtfTrack` no longer overwrites `.height` during
  layout.
- **Documented install name.** The install command is `pip install
  GenomeViewer`; the import namespace remains `pygv`.

## Migration checklist

1. Confirm the environment runs Python 3.10 or newer.
2. Replace `.height` reads used for layout with `layout_height()`.
3. Move `plot_type` and palette arguments from positional to keyword form.
4. Rename or remove unsupported keywords; unknown keys now fail.
5. Switch compatibility aliases to their canonical field names.
6. Stop reading private file-handle attributes such as `_bam` and `_bw`.

For the current field names, defaults, aliases, and accepted literals, see the
generated {doc}`api/tracks` and {doc}`api/viewer` reference.
