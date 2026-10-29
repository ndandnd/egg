"""Independent exact interval checker; no artifact access or dispatch side effects.

check accepts admitted compact metadata, not native output. Provenance string
identity checks are necessary but never establish authenticity on their own;
the frozen consumer must bind those strings to admitted immutable buffers.
"""
from fractions import Fraction


def _q(x):
    if isinstance(x, bool) or isinstance(x, float):
        raise ValueError('exact rational required')
    return Fraction(x)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def contains(interval, tau):
    tau = _q(tau)
    if interval['empty']:
        return False
    lo, hi = interval['lower'], interval['upper']
    return ((lo is None or tau > lo or
             (tau == lo and interval['lower_closed'])) and
            (hi is None or tau < hi or
             (tau == hi and interval['upper_closed'])))


def intersection(f0, inequalities):
    """Intersect tau >= -f0 with alpha+beta*tau > 0 exactly."""
    lo, lc, hi, hc = -_q(f0), True, None, False
    impossible = False
    for alpha, beta in inequalities:
        alpha, beta = _q(alpha), _q(beta)
        if beta == 0:
            impossible |= alpha <= 0
        elif beta > 0:
            endpoint = -alpha / beta
            if endpoint >= lo:
                lo, lc = endpoint, False
        else:
            endpoint = -alpha / beta
            if hi is None or endpoint <= hi:
                hi, hc = endpoint, False
    empty = impossible or (hi is not None and
                           (lo > hi or (lo == hi and not (lc and hc))))
    return dict(empty=empty, lower=lo, lower_closed=lc,
                upper=hi, upper_closed=hc)


def _identity(authority):
    # These are asserted transfer facts checked against pinned buffers by caller.
    for name in ('tree_source', 'tree_control', 'tree_artifact',
                 'mixture_source', 'mixture_control', 'mixture_artifact',
                 'descriptor_revision', 'case_token', 'supply_token',
                 'physics_token'):
        _require(isinstance(authority[name], str) and bool(authority[name]), name)
    for name in ('tree_complete', 'resource_pass', 'all_states_delivered',
                 'source_bound_closeout', 'components_admitted',
                 'full_replenishment', 'nonnegative_nonfee_costs',
                 'nonnegative_movement_energy', 'nonnegative_quadratic',
                 'fee_only_ops', 'unchanged_feasibility'):
        _require(authority[name] is True, name)
    _require(authority['minimum_fleet'] == 2, 'minimum fleet')
    # Explicit cross-package identities prevent a mixed-case/target transfer.
    for name in ('descriptor_revision', 'case_token', 'supply_token', 'physics_token'):
        _require(authority['tree_' + name] == authority[name], 'tree ' + name)
        _require(authority['mixture_' + name] == authority[name], 'mixture ' + name)


def check(fields, proposed=None):
    """Return exact sufficient tau/fee intervals or raise ValueError/KeyError.

    Required top-level keys: f0,L2,U,tau0,mixture,floor,authority.
    authority additionally binds original_fee, tree_L2, tree_target_U and
    mixture_U. Optional proposed must equal the complete returned tau interval.
    """
    f0, lower, upper, nominal = (_q(fields[k]) for k in ('f0', 'L2', 'U', 'tau0'))
    _require(f0 > 0, 'positive original fee')
    authority = fields['authority']
    _identity(authority)
    _require(_q(authority['original_fee']) == f0, 'changed original fee')
    _require(_q(authority['tree_L2']) == lower, 'changed lower')
    _require(_q(authority['tree_target_U']) == upper ==
             _q(authority['mixture_U']), 'changed upper')
    mix = fields['mixture']
    w = _q(mix['w'])
    _require(0 <= w <= 1, 'weight')
    counts = [_q(mix[k]) for k in ('N0', 'N1')]
    _require(all(n.denominator == 1 and n >= 2 for n in counts), 'component counts')
    ops = [_q(mix[k]) for k in ('ops0', 'ops1')]
    _require(all(o == f0*n for o, n in zip(ops, counts)), 'component operations')
    nbar = (1-w)*counts[0] + w*counts[1]
    mixed_ops = _q(mix['mixed_ops'])
    _require(mixed_ops == (1-w)*ops[0]+w*ops[1] == f0*nbar,
             'mixture operations')
    floor = fields['floor']
    if floor['kind'] == 'affine':
        a = _q(floor['A'])
        _require(a >= 0 and _q(authority['affine_floor']) == a, 'affine floor')
        three = 3*f0+a
    elif floor['kind'] == 'three_plus':
        three = _q(floor['L3'])
        _require(authority['three_plus_algebraic_floor'] is True and
                 _q(authority['L3']) == three, 'three-plus floor')
    else:
        raise ValueError('floor kind')
    inequalities = [(lower-upper, 2-nbar), (three-upper, 3-nbar)]
    interval = intersection(f0, inequalities)
    # Direct evaluation is independent of endpoint manipulation.
    _require(f0+nominal >= 0 and
             all(a+b*nominal > 0 for a, b in inequalities), 'nominal not strict')
    _require(contains(interval, nominal), 'nominal interval mismatch')
    if proposed is not None:
        _require(proposed == interval, 'proposed interval mismatch')
    # Endpoint checks catch openness errors independently of the formula branch.
    for side in ('lower', 'upper'):
        endpoint = interval[side]
        if endpoint is not None:
            direct = f0+endpoint >= 0 and all(a+b*endpoint > 0 for a,b in inequalities)
            _require(direct == interval[side+'_closed'], 'endpoint inclusion')
    return dict(status='CERTIFIED_SUFFICIENT_REGION', tau_interval=interval,
                fee_interval=dict(interval,
                    lower=None if interval['lower'] is None else interval['lower']+f0,
                    upper=None if interval['upper'] is None else interval['upper']+f0),
                Nbar=nbar, inequalities=inequalities, nominal_tau=nominal,
                nominal_gap_lower=min(a+b*nominal for a,b in inequalities),
                scope='fixed mixture and transferred lower bounds; not maximal')


def literal_qualification():
    """Prospective arithmetic controls; never invoked on import."""
    cases = [
        (2, [(1,1)], dict(empty=False,lower=-1,lower_closed=False,upper=None,upper_closed=False)),
        (2, [(1,-1)], dict(empty=False,lower=-2,lower_closed=True,upper=1,upper_closed=False)),
        (2, [(1,0)], dict(empty=False,lower=-2,lower_closed=True,upper=None,upper_closed=False)),
        (2, [(0,0)], dict(empty=True,lower=-2,lower_closed=True,upper=None,upper_closed=False)),
        (2, [(0,1),(0,-1)], dict(empty=True,lower=0,lower_closed=False,upper=0,upper_closed=False)),
        (2, [(2,1)], dict(empty=False,lower=-2,lower_closed=False,upper=None,upper_closed=False)),
    ]
    for f0, rows, expected in cases:
        _require(intersection(f0, rows) == expected, 'literal intersection')
    _require(not contains(intersection(2, [(2,1)]), -2), 'strict fee coincidence')
    _require(contains(intersection(2, [(3,1)]), -2), 'closed fee boundary')
    _require(not contains(intersection(2, [(0,1),(0,-1)]), 0), 'empty singleton')
    return dict(status='PASS', arithmetic_controls=len(cases)+3,
                transfer_controls='consumer must exercise check with frozen literal metadata')
