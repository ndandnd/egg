# Runnable QP baseline diagnostic

The isolated runner is `src/experiments/qp_baseline_diagnostic.py`; the
batch wrapper is `src/cluster/qp_baseline_diagnostic.sbatch`. The exclusive
attempt is `result/qp_baseline_diagnostic/20260929-attempt1`. The six-cell
design and interpretation limits are in [DESIGN.md](DESIGN.md).

Pure design preview, without optimizer execution:

```sh
PYTHONPATH=src python -m experiments.qp_baseline_diagnostic design
```

Focused checks:

```sh
python3 -m unittest src.tests.test_qp_baseline_diagnostic
bash -n src/cluster/qp_baseline_diagnostic.sbatch
```

The batch wrapper freezes and preflights on the compute host, then supervises
six individually capped children. Its sibling wrapper receipt records setup,
freeze, preflight and supervise outcomes even if an early phase fails.
Raw events/native results, compact six-row accounting, supervisor receipt
and manifest remain in the new sealed attempt for independent review.
No old retrieval or native-LP result is retried or relabeled.
