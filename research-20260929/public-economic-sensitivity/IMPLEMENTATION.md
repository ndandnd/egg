# Implementation scope

`public_economic_sensitivity.py` reconstructs the two DOI-pinned public
depot cases via the existing public-case adapter, validates their original
identities, then uses `dataclasses.replace` to change only the fee and name.
Every market is constructed from declared coefficients and receives its own
identity. Freeze and preflight repeat the deterministic design and source
hash checks on the compute node. Source pins include the physical input
payload, solver/driver code, analytical grid and these protocol files.

Planner/response call the existing native path-flow functions. Hull uses the
existing compact physical-pricing oracle and numerical-QP restricted-master
proposal; replay/assessment functions are reused. No solver core or native
cut is changed. Stage admission requires a successful on-time receipt,
compatible case/market/state/policy, finite ordered bounds and physical
replay. An ineligible response remains a declared row without a solve.
Derived gap/regret is missing when its inputs are incomplete or incompatible;
failed and late rows retain paid time and raw status. The analytical floor
grid is checked against the base public case identity and requested scenario,
then carried in a separate field with exact ideal-model scope.
