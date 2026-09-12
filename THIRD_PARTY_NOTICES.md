# Third-party notices

The PyGV documentation is distributed under GPL-3.0-or-later (see
[`LICENSE`](LICENSE)). This file records the third-party components and assets
that the documentation site reproduces or depends on, together with the notices
required by their terms.

## Theme and build tooling

The site is built with third-party Python packages that are installed as build
dependencies and are not vendored in this repository. Their license texts ship
with the installed distributions.

| Component | Copyright | License |
| --- | --- | --- |
| Sphinx | Sphinx contributors | BSD-2-Clause |
| MyST-Parser | Executable Book Project contributors | MIT |
| PyData Sphinx Theme | PyData contributors | BSD-3-Clause |
| Sphinx-Gallery | Sphinx-Gallery contributors | BSD-3-Clause |
| Matplotlib | Matplotlib Development Team | Matplotlib license (PSF-based) |

## Rendered example data

The Complete Gallery renders the example scripts and data files owned by the
PyGV code repository. Those files are not copied into this repository's history;
they are read from the pinned code checkout at build time. The rendered pages
may display images derived from the following third-party datasets.

| Data | Source | Terms |
| --- | --- | --- |
| K562 DNase-seq tracks | ENCODE (ENCFF530BKH, ENCFF413AHU) | ENCODE data are freely available; cite the ENCODE Consortium |
| K562 H3K27ac ChIP-seq track | ENCODE (ENCFF779QTH) | As above |
| K562 GRO-cap tracks | ENCODE / Kruesi et al. | As above |
| `gencodeV24.sub` annotation | GENCODE release 24 (Ensembl) | GENCODE/Ensembl data are freely available; cite the GENCODE Consortium |
| TREM2-locus GWAS summary statistics | Bellenguez et al., *Nature Genetics* (2022) | Reuse is governed by the originating publication and data provider; confirm terms before redistribution |

The ENCODE, GENCODE, and GWAS datasets are rendered solely to illustrate the
examples. Rendering them does not relicense them. Before publishing derived
figures, verify that each dataset's own terms permit the intended use and retain
the corresponding attribution.
