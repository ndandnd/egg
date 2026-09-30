# Graph v6 focused checks

GPT-6.1 Sol implemented the package and reported ten focused synthetic fixtures passing in 2.95 seconds, shell syntax validation of the Slurm wrapper, and Python compilation of the model, training CLI and probe supervisor. No campaign dataset was fitted during implementation.

The fixtures exercise graph topology and parallel movements, node/edge permutation behavior, disconnected batching, equal timetable/source/movement weights, parameter counts and autograd, numeric checkpoint roundtrips, inner stopping and architecture selection, exclusion of outer inputs until selection is persisted, typed runtime/child-signal failures and exclusive attempts. The final budget fixture verifies that a partly accumulated gradient is discarded and the best completed epoch restored when a soft time limit is reached.

Local fixtures use macOS PyTorch 2.4.1 and scikit-learn 1.6.0. They validate code behavior, not the pinned Linux runtime. The separate Linux environment has PyTorch 2.4.1+cpu, NumPy 1.26.4, SciPy 1.13.1, scikit-learn 1.7.2 and joblib 1.5.2; dependency checks and login imports passed. Its CPU wheel hash and complete dependency lock are recorded in ROUTE_GRAPH_ENVIRONMENT.json. Login imports do not establish compatibility on a compute node.

Every prospective task must pass the native import, operator, autograd and numeric checkpoint probes on unicorn-cpu-75 before bank loading. Probe failures stop the task and remain in its receipts. The immutable source, protocol, runtime receipt and lock must be committed before dispatch. Independent review is recorded separately; no complete-bank prediction replay or learned route-benefit claim has yet been made.
