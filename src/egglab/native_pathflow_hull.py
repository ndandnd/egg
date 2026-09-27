"""Explicit compact-pricing option for the shared native-hull coordinator.

No global mutation, copied certificate logic, or native optimizer on import.
"""
from egglab import native_hull as hull
from egglab import native_pathflow as pathflow

ORACLE_ID = pathflow.FORMULATION
EXTRACTION_POLICY = pathflow.EXTRACTION_POLICY
SCHEMA = hull.SCHEMA
Budget = hull.Budget
Market = hull.Market


def state_identity(case, market, arm, state_index, budget):
    return hull.state_identity(case, market, arm, state_index, budget,
        oracle_id=ORACLE_ID, extraction_policy=EXTRACTION_POLICY)


def _pricing(case, prices, budget, record=None):
    result = pathflow.solve_pricing(case, prices, budget, record=record)
    if result.get('formulation', ORACLE_ID) != ORACLE_ID:
        raise ValueError('Compact oracle returned another formulation')
    if result.get('status') in ('certified', 'bounded') and result.get('plan', {}).get('formulation') != ORACLE_ID:
        raise ValueError('Compact oracle witness returned another formulation')
    if (result.get('extraction_policy') != EXTRACTION_POLICY
            or result.get('plan', {}).get('extraction_policy') != EXTRACTION_POLICY):
        raise ValueError('Compact oracle extraction policy mismatch')
    # The qualified compact driver tags raw snapshots and plans, but its V1
    # top-level result has no formulation field. Tag this explicit dispatch
    # only after validating the physical plan's existing provenance.
    return {**result, 'formulation': ORACLE_ID}


def certify(case, market, budget=Budget(), *, arm='cold', state_index=0,
            previous=None, expected_previous=None, record=None):
    return hull.certify(case, market, budget, arm=arm, state_index=state_index,
        previous=previous, expected_previous=expected_previous, record=record,
        pricing_oracle=_pricing, oracle_id=ORACLE_ID,
        extraction_policy=EXTRACTION_POLICY)
