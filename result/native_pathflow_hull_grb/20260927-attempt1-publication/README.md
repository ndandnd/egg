# Public-copy selection for GRB hull qualification attempt 1

This sibling directory describes a prospective public copy; it does not alter
or publish the immutable raw attempt. The raw `MANIFEST.json` lists 66 files.
`PUBLIC_MANIFEST.json` identifies eight complete per-control `stdout.txt`
files omitted from the public selection, with original bytes, SHA-256 and
reason. Each omitted file is an exact repetition of the same three-line
license/backend initialization diagnostic template already screened in the
physical GRB attempt; these files contain no solution content. The other 58
manifested files remain byte-for-byte unchanged, as does the original
`MANIFEST.json` itself. An exact `.gitignore` pattern prevents accidental
staging of those eight stdout files.

All eight control input, event, result and receipt files are retained without
rewriting. Controller and wrapper stdout contain JSON receipts and are
retained, along with the wrapper launch/receipt, supervisor launch/receipt,
all five sibling `.launch` files, and the adjacent INTENT/SUBMITTED sentinels.
Routine work directories and scheduler job IDs are ordinary provenance and
are not redacted. Slurm stdout/stderr and the eight omitted originals remain
in the private sealed transport archive at
`/Users/nadan/Documents/ChatGPT/egg/research-20260927/cluster/grb-hull-559602/hull-559602-transport.tar`.

The public selection is **not** a full raw archive: verification of the
original 66-entry manifest and independent scientific admission requires the
omitted originals. The private local raw attempt and its manifest remain
unchanged. This note records file selection only; it does not assess hull
certificates or authorize the nonlinear public pilot.
