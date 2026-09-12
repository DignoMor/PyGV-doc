# GenomeViewer

`GenomeViewer` is the {term}`genome viewer`: it owns track order, figure
layout, shared annotations, and the render lifecycle. Tracks render in
registration order over one zero-based, half-open {term}`genomic interval`.
See {doc}`../concepts` for the concepts behind these operations.

```{eval-rst}
.. autoclass:: pygv.viewer.GenomeViewer
   :members:
   :show-inheritance:
```
