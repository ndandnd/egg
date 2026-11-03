# V7 cost-component diagnosis review

**Verdict: no material arithmetic or qualification issue found.** The companion uses the fixed common-15 cohort from the reviewed v7 ledger and hash-pinned saved replay outputs. It adds no model inference, plan replay, optimization, promotion, or retry.

The exact rational identities hold for all three arms: operations + linear tariff + quadratic supply = bill; linear tariff = high-tariff quantity reference + cheap-period discount. On the common 15, fleet and operations deltas are zero. The graph bill gap (+4.599760) decomposes into +3.919111 linear and +0.680649 quadratic. Its linear gap further decomposes into +0.499111 from total grid energy at the high-tariff reference and +3.420000 from less charging in cheap periods. This is an accounting identity over saved loads, not a causal tariff or route counterfactual.

The reported topology counts agree with the ledger: graph differs from the winning source on 13/15 groups and is novel against the two-source bank on 11/15. The report does not infer cost benefit from novelty. Group 10069 remains absent for family/graph due to the existing cover timeout; tabular is retained both for that group (+100 operations, +13.915027 supply) and in its separate all-16 mean (+6.250000 operations, +1.320038 supply). No missing cost is imputed.

I independently checked the displayed common-15 mean component and tariff-rebasing identities against the exact rational values in the JSON. The cost-component report preserves the previously disclosed ±0.01 descriptive tolerance and the v7 failures; it makes no causal, optimality, or speedup claim.
