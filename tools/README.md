# Documentation build tools

These tools build the public PyGV documentation site and assemble it into one
GitHub Pages artifact. The site publishes two channels from a single artifact:

- the **stable** channel at the artifact root, built from the documentation and
  code `main` pair;
- the **development** channel under `/dev/`, built from the documentation and
  code `dev` pair.

## Single-channel build

`tools/build_docs.py` builds exactly one channel. It reads that documentation
branch's `code-ref.json`, verifies that the pinned code commit belongs to the
named code branch, installs (or imports) that checkout, and runs Sphinx with
warnings treated as errors. The gallery is executed from the paired checkout and
written to a revision-keyed, disposable directory.

Local build against an existing checkout:

```bash
MPLBACKEND=Agg python tools/build_docs.py \
  --code-dir ../code \
  --no-install \
  --outdir build/development
```

After the build, run the strict suite against the rendered output:

```bash
MPLBACKEND=Agg PYGV_DOC_BUILD=build/development python -m pytest tests -q
```

The suite covers authored content, the rendered API reference, the executed
gallery, built-output link resolution, and the agent-readable artifacts
(`llms.txt`, per-page `.md` alternates, and provenance).

## Two-channel assembly

`tools/assemble_site.py` combines two already-built channel directories into a
single fresh aggregate. It validates each channel's provenance, `llms.txt`, and
Markdown alternatives before copying, then re-validates the aggregate so both
channels are present. It never writes a `CNAME` or a historical version
directory, and it always recreates the output from scratch so one channel
cannot erase the other.

```bash
python tools/assemble_site.py \
  --stable build/stable \
  --development build/development \
  --outdir build/site
```

The result has the stable channel at the root and the development channel under
`build/site/dev/`. All links in both channels are relative, so the same artifact
is correct at the Pages project root and beneath `/dev/`.

Because each published channel is paired to its own documentation branch, a real
stable build requires the documentation `main` branch to contain this tooling.
Until then, exercise the assembler with synthetic channel fixtures (see
`tests/test_assemble_site.py`) or a locally built development channel plus a copy of
it relabeled with the stable provenance.

## Continuous integration

`.github/workflows/docs.yml` builds and validates both channels for every push
to documentation `main` or `dev`, for manual dispatch, and for pull requests.
Pull-request runs use read-only permissions, never invoke Pages deployment, and
upload an ordinary inspectable `docs-site` artifact. Only the non-PR deploy job
receives `pages: write` and `id-token: write`, uploads the Pages artifact, and
deploys it.

To verify the pipeline locally without pushing:

```bash
MPLBACKEND=Agg python tools/build_docs.py --code-dir ../code --no-install \
  --outdir /tmp/docbuild
MPLBACKEND=Agg PYGV_DOC_BUILD=/tmp/docbuild python -m pytest tests -q
```
