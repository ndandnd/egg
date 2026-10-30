# One complete identifier-registry inspection, no rows or generation

The earlier successful max8-line schema read exposed base_id entries but could
not inspect the full group crosswalk. Preserve that read/meter; do not repeat it.
New question: what explicit identifier mapping is present in the full registry?

One new metered inspect_train_registry.py command,10CPU/20wall,8MiB input cap,
only the same whitelisted TRAIN pool_manifest.json. Output only schema keys and
whitelisted group/base/case/alias identifiers; never follow a row or data path.
No weights, model, hash, inference, generation, replay or solver. Exact command:
PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -p -o research-20261025/warm_replication/train-registry-time.txt .venv-local/bin/python research-20261025/warm_replication/inspect_train_registry.py

This is a separately bounded preparatory metadata inquiry, not the yet-unfrozen
eight-hour numerical campaign. Carry its external measured cost forward into
historical process accounting before the campaign's final budget/command is
selected; no refund or assertion of whole-session CPU. Exclusive output
train-registry-schema.json. If mapping remains incomplete, disclose that and
do not descend into rows/labels/DEV/TEST or infer aliases from namespace spelling.
Parent inspected this small static script before the once-only read.
