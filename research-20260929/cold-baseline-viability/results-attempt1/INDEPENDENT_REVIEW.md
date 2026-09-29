# Independent result receipt check

The attempt is sealed and internally accounted. The manifest lists 49 files; its inventory exactly matches the attempt tree, with no missing, extra, or hash-mismatched files. The summary accounts for all six declared cells exactly once. Each cell has a manifest-covered receipt, raw result, and assessment, and all six receipts are on time with complete evidence and non-null native lower and upper bounds.

The supervisor returned 0, the child returned 0, there was no timeout, the process group is quiescent, the stable seal is true, and frozen source hashes remained unchanged. The sibling Slurm wrapper receipt also reports return code 0 with freeze, preflight, and supervise all returning 0; elapsed time was 112 seconds on the requested one CPU / 8192 MB allocation.

Outcomes match the screen design:

| Case size | `source0` | `target` |
|---|---|---|
| n08 | `budget_exhausted`, 3 pricing calls | `certified`, 2 calls |
| n16 | `budget_exhausted`, 4 pricing calls | `certified`, 2 calls |
| n24 | `budget_exhausted`, 5 pricing calls | `certified`, 3 calls |

All three source0 stops report rational-polishing projected bit-size budget exhaustion; no runtime failure or late cell occurred. These rows still contain complete, replay-assessed native enclosures, but `budget_exhausted` is not a certification. The three target `certified` statuses refer to the configured native algorithm on these generated development cases only. All reported bounds are native solver / physical-replay tolerance-conditional values. An `_exact` field denotes the exact rational representation of a stored value; it is not an ideal-hull certificate.

This was a bounded metadata/receipt review: I did not inspect event JSONL, rerun tests, or run an optimizer or cluster job.
