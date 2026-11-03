# Pricing-start core CI receipt

Source: `d0df8d7440d026aabe236bafa3c8031b31b14bc9`.
Workflow: [CI 36435346518](https://github.com/ndandnd/egg/actions/runs/36435346518).

The complete CBC-only gate passed on attempt 1; the test job took 4 minutes
19 seconds. Dependency installation, whitespace/conflict checks, shell syntax,
the complete pytest suite and frozen journal-evidence reconstruction passed.
No workflow changes or retry were needed.

Local validation is recorded separately: 40 focused pure tests and one bounded
CBC functional check. The latter preceded the final pure-tested discrete-variable
guard. This CI gate verifies repository compatibility; it does not measure
Gurobi performance or execute the prospective cold/start comparison.
