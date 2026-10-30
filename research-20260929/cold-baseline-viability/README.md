# Runnable cold-baseline viability package

The six-cell design is in [DESIGN.md](DESIGN.md). The isolated runner is
`src/experiments/cold_baseline_viability.py`; the batch wrapper is
`src/cluster/cold_baseline_viability.sbatch`. The exclusive new attempt is
`result/cold_baseline_viability/20260929-attempt1`. The wrapper freezes and
preflights on the compute host, then supervises six separate children with
hard caps; it writes a sibling wrapper receipt even if freeze or preflight
fails. No old retrieval attempt or protocol is changed.

Pure design preview, without an optimizer call:

```sh
PYTHONPATH=src python -m experiments.cold_baseline_viability design
```

Focused local check:

```sh
python3 -m unittest src.tests.test_cold_baseline_viability
bash -n src/cluster/cold_baseline_viability.sbatch
```

Execution is left to the coordinating task after source review and publication.
The sealed attempt retains raw events, native results, six compact summary rows,
supervisor receipt and manifest. A later independent review determines which
returned native enclosures can be scientifically reported; missing component
times never become zero.
