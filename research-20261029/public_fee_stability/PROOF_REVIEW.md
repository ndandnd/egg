# Independent source-only proof and checker review

## Mathematical assessment

The stated sufficient interval argument is valid under the declared invariant model and qualified transfers. For every physical two-bus plan the original bound L2 shifts by exactly 2τ. A global original lower is a valid, possibly weaker, choice of L2. It cannot instead be shifted by 2τ for all fleet counts.

For N≥3, nonnegative new fee f0+τ and the independent affine non-fee floor A imply Jτ≥N(f0+τ)+A≥3(f0+τ)+A. This argument covers arbitrarily many buses without an artificial fleet cap. A transferred L3 is sufficient only when its algebraic authority establishes L3≤3f0+A; an arbitrary old bound on three-plus fleets is not by itself sufficient to justify shifting it by 3τ when τ is negative. The proof and field notes state this condition correctly. Zero and one bus must remain independently physically excluded.

For the admitted fixed mixture, unchanged feasible plans and unchanged weight give the exact fee slope Nbar=(1−w)N0+wN1. The quadratic supply term is unchanged at its mean load. Thus its original admitted objective U shifts by Nbarτ, irrespective of whether the mixture was originally optimal along its segment. New hull alternatives can only lower CH further. Both strict affine comparisons are necessary for this particular sufficient certificate and together prove a positive global gap. Their intersection is not asserted to be the maximal stability region.

The nonnegative-fee boundary is closed. Each finite boundary originating in a strict comparison is open, even when it coincides with that fee boundary. A zero-slope comparison is vacuous if its constant is positive and makes the intersection empty otherwise. These rules cover unbounded and empty intersections and simultaneous/coincident restrictions. Exact equality never certifies a positive gap.

## Checker API and authority boundary

`checker.py` provides `check(fields, proposed=None)`, `intersection(f0, inequalities)`, `contains(interval, tau)` and `literal_qualification()`. It performs no artifact reads or computation at import. Fractions, integers and rational strings are accepted; floats and booleans are rejected as rational inputs. `check` fails closed on missing required keys, invalid identities, nonintegral component counts, changed objectives/fees, absent bound authority, or a supplied nominal point outside either strict comparison. Exceptions are admission failure, not a reported empty public stability result.

Required fields are f0, L2, U, tau0, mixture, floor and authority. Mixture contains w,N0,N1,ops0,ops1,mixed_ops. Floor is either `{kind:'affine',A:...}` or `{kind:'three_plus',L3:...}`. Authority requires nonempty immutable source/control/artifact identities, matching tree/mixture case/descriptor/supply/physics tokens, explicit successful transfer assertions, original_fee/tree_L2/tree_target_U/mixture_U, minimum_fleet=2 and the original physical sign/fee-only invariants. The affine route additionally binds affine_floor; the L3 route additionally binds L3 and three_plus_algebraic_floor=true. Exact key names are in the small source and must be used by the prospective consumer.

The checker does not authenticate an asserted boolean or revision string. The separately frozen consumer must compare these fields to pinned admitted buffers and approved fixed paths. In particular, a tree global lower may be relabeled L2 only with an explicit consumer assignment explaining its restriction to the two-bus subset; this is not a claim that the tree supplied an exactly-two optimum. Changed authority tokens cannot be accepted merely because both packages copy the same attacker-supplied token.

The output supplies exact tau and fee intervals, openness flags, two affine comparisons and a direct nominal gap lower. An optional proposed interval must match exactly. Independently evaluated endpoint inclusion checks supplement the endpoint construction. The nominal point is also directly evaluated, serving as an exact interior/member check. No decimal output decides membership.

## Prospective qualification and remaining integration

The included unexecuted arithmetic qualification specifies positive, negative and zero slopes, a contradictory intersection, a strict coincident endpoint, a closed fee endpoint and exclusion of an empty singleton. Consumer literal controls must additionally exercise missing fields, noninteger/incorrect component counts, inconsistent mixed operations, out-of-range weight, changed original fee/case/supply/upper/lower, absent algebraic L3 authority, an altered proposed openness flag and a nominal point on a strict boundary. Such malformed-transfer controls are meaningful only when passed through `check`, rather than through the interval primitive alone.

No numerical public values, packets, raw compressed artifacts, native code, old physical replays, hashes, imports, execution, tests or commits were consumed or performed for this review. This is a source-only prospective method, not a qualified interval result. Field-authority provenance integration and literal qualification must pass before any public interval is reported.
