# Feasible pool pilot implementation

`src/experiments/feasible_pool_pilot.py` runs 24 declared development hull cells: four fixed physical cases, two markets per case, and three arms per market. It imports the previous screen's case builders, market definitions, cold-hull budget, replay assessment, child receipt, and process-group cleanup. Its own frozen design pins all cases, markets, arm controls, budgets, source hashes, and the execution commit.

The legacy arm uses the default cold hull. Both reserve arms request a 10-second native pricing reserve. The feasible-pool arm uses a fresh retained state 0; state 1 may import only its own state-0 replayable pool from a successful, on-time child receipt. A certified predecessor is not required. Failed or incomplete predecessors make state 1 ineligible. The core replays imported columns and starts with fresh target-market bounds and weights.

The controller records all 24 rows, including ineligible cells. The supervisor reconciles missing rows after abnormal termination, kills and checks the controller process group before sealing, and checks source hashes again. The Slurm wrapper writes its receipt beside the sealed attempt directory. This is a development pilot, not independent result validation or an ML split.
