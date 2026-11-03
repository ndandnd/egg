# Independent interpretation of fee attempt01

Read only the new compact results, owner receipt and worker receipt. No historical inputs, compressed packets, physical replays, hashes or recomputation were used. External meter values below were supplied by the parent closeout; no separate meter file was reopened.

## Outcome and closure

The new package reports COMPLETED and CERTIFIED_SUFFICIENT_REGION. ADMISSION, Q0 and PUBLIC_INTERVAL are all DELIVERED; failure is null, resource_pass is true and native_calls is zero. Owner receipt binds source `872e38aef22dd4f736daa4862fa46b4d38af811b`, child 89046 exit 0 and reaped=true. Worker and master summaries agree. The supplied frozen control is `d37fea3b`.

The compact result gives Nbar=2 and the sufficient fee interval (fcrit,+∞), with an **open** lower endpoint

    fcrit = 207144809919773459175544589361909362103645314362363582220429474260291397350199127418953716376701502557
            /3271461678119739162838778949479488288386427183774469641575516104263648171125254058271345771399872512.

The result also directly certifies nominal τ=0. Its first affine comparison has zero slope and a strictly positive constant; its second has slope one. Thus increasing the original fee 100 cannot reduce this certificate's gap lower. For every fee f≥100, **support failure persists**, with at least the same positive lower bound reported at the nominal fee. This means absence of own-load support for a globally optimal whole-fleet participant under the original qualifications; it does not mean support is restored.

For certified lower fees, the second comparison decreases as the fee falls. The reported guarantee is the minimum of its increasing affine term and the fixed positive two-bus comparison. It can remain on that constant plateau before the higher-fleet comparison becomes limiting; as f approaches fcrit from above, the guaranteed positive margin tends to zero. The open boundary is essential. The certificate does not establish a positive gap at fcrit, nor establish zero gap or support restoration there or below it.

## Scope

This is a sufficient interval from one fixed admitted mixture and transferred bounds. It is not the maximal fee-stability interval, an exact phase diagram, or an exact value function. It varies only the used-bus fee while retaining original services, movements, inventories, resources, supply coefficients and non-fee costs. It does not establish robustness to battery losses, changed charging access, timetable/energy uncertainty, tariffs or participant rights. The same-bound conclusion at arbitrarily high fees is an algebraic consequence of both witness components using two buses and all larger fleets paying at least three fees; it is not a calibrated practical welfare claim or ML result.

## Resource interpretation

The parent supplied external meter totals 0.29 CPU seconds and 0.43 wall seconds, with retained CPU 0.31. Owner inclusive observation is 0.288481 CPU seconds and 0.3871352504938841 wall seconds; peak observed RSS is 23117824 bytes. Worker observation is nested in that owner charge and must not be added again. The supplied retained CPU covers the reported owner and external rounded CPU observations. These observations fit the declared 120 CPU/180 wall package and 512 MiB observed per-process gate. They represent this new metadata/interval package only; historical certificate acquisition costs remain separate and retained.

**Interpretation PASS.** The compact result supports the stated sufficient open interval and uniform nominal gap guarantee for all fees at least 100, with the scope limits above. No new computation was performed for this review.
