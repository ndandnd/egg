# Grid-information learning: completed, no demonstrated neural increment

Sourcecf110af92471d4579d3c27952eef936a34d151aa/control6e4b7101. Owner13232 exited0; its sole owned child84240 exited0 and was reaped. One source admission/owner/worker/inlineREADOUT, no retry. All24 physical groups distinct.128training/validation bank acquisitions qualified;768/768 test assignments were strict physical deliveries with nativeOPTIMAL, all references qualified, no failures/missing/unattempted states. These are8 evaluation timetable groups with8contexts each, not768 independent instances. All native statements concern the declared exact-four-fleet graph and numerical tolerances.

## The research question

Unknown background load can make learning valuable even when known-price optimization is cheap. Every predictor here received the same observable features and then the same joint free-path/continuous-charging optimizer. Complete grid outcomes supplied supervision. The nonlinear system objective, backgroundU and curvatureb were explicit. Strong controls included correctly specified quadratic regression, linear ridge and boosted trees. This was a new synthetic mechanism experiment, not real electricity forecasting or V2G, and generic decision-focused prediction is prior art.

Mean conditional expected electricity costs, excluding constant operations400:

| Method | Expected cost | RMSE to conditional background mean |
|---|---:|---:|
| Unconditional estimated mean |71.989536|11.7311|
| Linear ridge |71.404118|4.1242|
| Quadratic ridge |71.352922|3.9902|
| Boosted trees |71.399253|4.6041|
| Small32×32 neural MSE |71.446528|7.4928|
| Larger128×128 neural MSE |71.368882|5.2307|
| Same-size decision-focused network |71.621344|8.0652|
| Trained blind neural MSE |71.993461|11.7917|
| Trained blind decision-focused |72.105702|12.1053|
| Conditional-mean joint reference |71.276929|0|
| Conditional-mean fixed-route reference |71.276929|0|

The information reference improved on the unconditional policy by0.9947648% mean paired ratio, positive8/8groups; descriptivet7interval[0.6711%,1.3185%]. It narrowly missed the frozen>1% investment rule. This does not imply a zero effect, statistical equivalence, or a sharp scientific boundary at1%. Its fixed-route counterpart matched joint expected cost to numerical roundoff: no incremental route-value mechanism was demonstrated. Charging information can matter without learning new service assignments.

Quadratic regression had the lowest expected cost among fitted methods. Its remaining conditional-mean-reference headroom was only0.1052607% of paired unconditional-policy expected electricity (derived by subtraction of existing complete paired contrasts, not a ratio of totals). This is a useful ceiling on the improvement over that classical baseline within this tested information/model scope, conditional on the numerical reference qualification. It does not certify unrestricted EVSP, unseen distributions or empirical savings. The selected larger MSE network gained0.8669658% over unconditional mean; the selected small network gained0.7580855%. Neither exceeded the strongest classical baseline on mean expected cost.

Decision-focused training lost0.3516379% against the same-size MSE predictor, and0.3741762% against quadratic ridge, in paired unconditional-electricity units; it lost to each of ridge/quadratic/boosted controls in all8groupmeans. It did improve on its trained blind counterpart by0.6789579%, positive7/8groups. Context information was useful, but the proposed loss did not turn it into a classical-baseline advantage. The registered learning screen failed with complete eligible comparisons.

Perfect realized information reached mean realized electricity70.840585 versus71.969556 for unconditional mean. It is a separate unattainable realized-cost reference. Its conditional expected cost71.639769 is not a Bayes-information benchmark: it adapts to future noise that is not observable before commitment. Expected and realized comparisons must not be conflated.

## Was the network simply too small?

Capacity mattered in this new task. The2334-parameter32×32 model was worse than the21534-parameter128×128 model: mean paired improvement0.1088803%, positive7/8groups. Both had two fixed initializations and validation-only selection. Thus the earlier broad interpretation that model size cannot matter would be wrong.

A separate256×256 network fit the32-row noiseless diagnostic to normalizedRMSE.009978815 in292updates, passing the frozen≤.01 check. Its privileged labels and model never entered production training/selection. All banks had8 distinct load vectors to6decimals, so the DFL surrogate was not trained on a completely constant action set. This establishes bounded interpolation/optimization and nontrivial bank variation, not universal model adequacy or generalization. Main MSE runs hit the500-update ceiling; convergence of every model is not proved. The larger model's selected training normalizedRMSE.08616 was below its validation.11397; a simple lack-of-capacity story does not explain the whole result.

The DFL result also has a concrete training-policy limitation. Its selected seed29/epoch4 had worse validation bank cost than its same-seed initial MSE model (72.02408 versus71.98868). Seed17/epoch2 did improve on its own initialization (72.03909 versus72.09533), but was not selected. Epoch0 was not eligible for DFL checkpoint selection in the frozen recipe, although the MSE model was retained as a separate mandatory comparison. This is not evidence that all decision-focused methods fail. The finite-bank softmin surrogate and checkpoint policy can contribute to its loss. No post-result checkpoint replacement, retraining or silent repair occurred.

The old GNN remains a different unresolved diagnosis: small architecture, incomplete economic inputs, incumbent-membership supervision and unknown convergence. This new test cannot retroactively rule out a better old model. It does show why merely increasing width is insufficient to establish a contribution here: a competent classical predictor already captures most of the tested information value, and no extra joint-routing value appeared.

## Resources and disposition

Full campaign69.16displayedCPU/82.36elapsed seconds; retained69.18CPU. Model fitting20.098221CPU/24.283317elapsed is INCLUDED, not added. Peak observed workerRSS360660992bytes; owner21266432bytes; configurednative1thread. All source admission, construction,128paid bank acquisitions, models, selection, inference,768testsolves, physical replay, writing and ownerpacketreading included. All learned approaches would pay their own acquisition/training cost in any deployment accounting; no free amortization or solver-only speedup is claimed.

Close this specific synthetic DFL proposal without promotion or a harder-case search. Positive evidence supports usable contextual grid prediction and demonstrates a real capacity effect, but not a novel joint EVSP–grid ML method beating strong controls. Further work requires a distinct substantive target with residual value beyond those controls, not a bigger network justified only by this result. No new cohort, model, retry, empirical dataset, V2G extension or automation is launched.
