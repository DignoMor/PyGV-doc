# Utilities

```{eval-rst}
.. autofunction:: pygv.utils.check_accessibility
```

`check_accessibility` performs side-effect-free source-location validation for
the plotting code path. It returns `True` when a local path exists and, only
when `allow_remote=True`, also accepts strings that begin with `http` or `ftp`.
Inaccessible locations raise `ValueError` by default, or return `False` when
`raise_except=False`.

It does **not** probe a remote endpoint over the network, and it does not
validate file contents or format. A remote string is accepted by prefix alone.
