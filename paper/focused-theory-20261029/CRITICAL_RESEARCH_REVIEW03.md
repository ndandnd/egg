# Adversarial scientific review after the public sign certificate

Read the current main narrative, heterogeneous theorem section, V2G section, public-case section and related work. This is a contribution/evidence review, not a repeat proof or source audit. No raw packets, computations, tests, imports, hashes, commits or new agents.

The public section now establishes a materially stronger result: exact separation on a varied-time complete scheduling instance, rather than unsupportedness of a selected incumbent. The abstract, introductory public-evidence paragraph, implications paragraph and conclusion in `main.tex` still describe the sign as unresolved. These are stale integration statements, not remaining research holes; they should be updated to match `public_case.tex` before the next draft is circulated. Preserve the distinction between a certified sign and unknown exact optima.

## Three remaining substantive holes

1. **Robustness and practical magnitude are not established.** The certified separation0.008790 is a lower bound on an unknown gap, not an estimate of its size. It establishes a mathematical obstruction in one synthetic ideal model but cannot support a claim of economically material loss. The analytical reserve/loss neighborhood and V2G examples do not transfer to the public varied-time model. In particular, changing charging losses, terminal conditions or access can change feasibility, and the small certificate margin alone supplies no physical-parameter robustness guarantee. The public timetable is useful as a structural existence example; its public provenance does not calibrate its energy coefficients or tariff.

2. **The narrow novelty/significance comparison remains incomplete.** Fixed-window lossless aggregation, matching convexity and nonconvex support are established. The theorem's value lies in the explicit interaction between service assignment, fleet cost and a shared gross connector, but a reviewer may still regard this as a straightforward tractable specialization. Zhou–An–Schmöcker2025 explicitly considers spare-bus V2G/cross-line operation, while its full formulation was inaccessible; the abstract cannot establish that a similar structural result is absent. V2G enriches the mechanism but is not a standalone novelty defense. The paper should state the exact classification as its contribution without elevating its generic ingredients.

3. **Independence is internal and the certificate is operationally complex.** The global result relies on an exact lower proof, separately admitted physical components, transfer authority and exact mixture upper. This is stronger than native agreement, but a fresh reader must still reconstruct a substantial provenance chain and trust that the admitted semantic model describes the stated schedule set. The existing independent semantic reconstruction and physical replay are important; neither is external replication. A concise machine-readable certificate index plus a human mathematical map from each certificate to the final inequality is more useful than another overlapping native run. Full optimum recovery is unnecessary, and no additional own-price query is needed for the sign.

## Best next research action: a prospective, certificate-based vehicle-fee stability interval

Prioritize one bounded analytical extension of the public result: vary only the used-bus fee, preserve the original physical case and supply function, and derive an exact sufficient interval on which the already certified separation survives. This addresses outcome sensitivity without inventing another empirical cohort, changing equipment or seeking a larger gap through outcome-guided sweeps. It does not turn synthetic prices into calibrated economics.

The construction is concrete. Let the original fee be f0, the certified two-bus physical lower be L2, the independently justified three-plus floor be L3, and the admitted two mixture components have bus counts N0,N1 and fixed rational weight lambda. Put Nbar=(1−lambda)N0+lambda N1 and let U be that mixture's original upper. With fee shift tau, the SAME physical component plans and mixture remain feasible and give a hull upper U+tau*Nbar. Every exactly-two-bus physical plan has objective shifted by exactly2tau, so its global lower is L2+2tau, without changing branch topology or rerunning a node solve. For all fleets N>=3 and nonnegative new fee, reconstruct the existing service-energy argument as 3(f0+tau)+a*service/eta. The one-bus obstruction is physical and unchanged.

Intersect the exact strict inequalities

`L2+2*tau > U+Nbar*tau`,

`3*(f0+tau)+a*service/eta > U+Nbar*tau`,

with `f0+tau>=0`. The interval containing tau0 is a rigorous robustness certificate. Do not assume both mixture components have two buses: read their already admitted source-bound counts. If they do, the two-bus separation is fee-invariant and only the higher-fleet exclusion imposes a boundary; otherwise the first inequality provides the correct additional endpoint. A fixed admissible mixture is sufficient; reoptimizing its weight is unnecessary. Report this as a sufficient certified interval, not the exact phase diagram or a numerical sensitivity experiment.

The bounded deliverable should be a short proposition/proof, exact source-bound count/constant table, and one independently hand-checked interval derivation. This can strengthen the public result beyond a single tuned fee without a new native solve, broad infrastructure or claims about losses/physical perturbations. If the interval is narrow, retain that honest finding rather than tuning another parameter. The useful scientific message is stability of a strict certificate under a clearly specified objective perturbation, not evidence of practical prevalence.
