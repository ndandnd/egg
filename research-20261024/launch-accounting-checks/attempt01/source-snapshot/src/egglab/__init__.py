"""egglab: Phase 0/1/2 experiment infrastructure for the price-maker EVSP.

Modules:
- instance:   EVSP instance model + synthetic generator (+ frozen-subset loader stub)
- market:     price/supply models (affine), welfare accounting, PWL segments
- solver:     MILP backend wrapper (Gurobi via python-mip if available, else CBC)
- evsp:       the EVSP MILP oracle, solution extraction, replay validation
- regimes:    uncontrolled / price-taker / strategic (B9) / dictator solves
- loops:      Phase-1 price fixed-point iteration with cycle detection
- boundary:   Phase-2 switch-boundary sweeps
- records:    the Phase-0 logging contract (JSONL run records with provenance)
- checkpoint: atomic checkpoints for preemption-safe restart
- collect:    aggregate JSONL records into CSV for analysis
"""

__version__ = "0.1.0"
