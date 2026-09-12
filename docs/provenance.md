# Build provenance

Every published channel is built from an exact pair of revisions. Signatures,
defaults, and gallery examples on this site come from the paired **code**
commit; the authored pages come from the exact **documentation** commit.

| Item | Value |
| --- | --- |
| Documentation channel | {{ doc_channel }} |
| Documentation commit | {{ doc_commit }} |
| Code repository | https://github.com/liyao001/PyGV |
| Code branch | {{ code_branch }} |
| Code commit | {{ code_commit }} |
| GenomeViewer version | {{ release }} |

The documentation repository records the paired code commit in its public
`code-ref.json` manifest, and the build refuses to run unless that commit
belongs to the named code branch. The stable channel at the site root describes
the code `main` branch; the development channel under `/dev/` describes the
code `dev` branch.

This pairing exists so that a reader can always reconstruct which public code
revision produced a page, and so that a release can be pinned in the private
release ledger.
