# Retrieval comparison: preflight failure, no solver outcomes

Job **584876** failed before the controller or any optimization began. Slurm
records FAILED (exit 1:0), 12 seconds elapsed, one allocated CPU and 8 GB requested
on unicorn-cpu-75. The wrapper records 7 seconds, all in setup, with preflight
returncode1. There is no supervisor receipt or successful experiment manifest;
the attempt directory contains only the frozen specification. All 48 planned
children are explicitly unstarted, with unavailable timing/bound fields. This
failure provides no evidence for or against any retrieval method.

The runner compared the complete environment dictionary, including
`platform.platform()`, for exact equality. The prospective freeze records login
kernel 6.8.0-136; scoped Slurm node metadata records compute kernel 6.8.0-138.
That observed difference alone necessarily causes the recorded generic failure
before the native-backend probe. Other failed predicates were not logged, so
this identifies a sufficient cause rather than claiming every other predicate
was observed to pass on the compute node.

The source, frozen specification, failure logs and receipts are preserved in the
private collection. Its frozen SHA matches the prelaunch pin. The public
[collection manifest](COLLECTED_MANIFEST.json) hashes every collected file;
it is a post-failure inventory, not a successful experiment seal. The
[complete failure receipt](FAILURE_RECEIPT.json), [wrapper receipt](wrapper_receipt.json)
and [preflight traceback](preflight_stderr.txt) preserve the observed failure.
Slurm elapsed and wrapper setup are overlapping measurements, not additive.
Earlier paid preparation and submission work remain in the parent launch and
preparation receipts. No job was retried, requeued or replaced.

A minimal source repair now compares software/package identity
strictly while recording host/kernel metadata separately, and identifies future
failed predicates explicitly. Nine focused pure tests pass, including rejection of changed Python builds.
The independent [repair review](REPAIR_REVIEW.md) found no blocker; publication
[full CI](https://github.com/ndandnd/egg/actions/runs/36471163895) also passed
for repair source `478d565` (test job 4m25s). It does not alter this attempt, its resource use
or its failure classification. The fixed comparison protocol forbids retries;
a replacement compute attempt is not launched by this repair package.
