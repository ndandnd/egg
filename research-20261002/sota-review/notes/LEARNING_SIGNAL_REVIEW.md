# Independent review of the learning-signal design

2 October 2026. A GPT-6.1 Sol writer prepared the protocol and a separate GPT-6.1 Sol reviewer checked it without data, models, cluster access or experiments. The parent reviewed the material objections before integration.

The review identified five issues:

1. **Collector leakage:** fitting the final model within folds is insufficient if the model collecting labels has already seen held-out groups. Register collector training provenance and exclude evaluation information at acquisition time.
2. **Undefined group-level gates:** 18 cells are not 18 independent timetables. Register progenitors, tariffs, budget aggregation and which groups enter the advancement threshold. Name the comparator for public deterioration.
3. **Failure accounting:** missing labels must not become negative examples; missing online references and jointly failed pairs must not vanish from promotion denominators. Freeze the numerical loss convention before launching.
4. **Resource feasibility:** 32 + 16.2 = 48.2 solver CPUh is correct, but the remaining budget must also cover all fits, preprocessing, replay, engineering checks and failed attempts. An arithmetic envelope is not evidence that training fits within it.
5. **Claim boundary:** choosing the best incumbent from the common pool isolates the value of target multiplicity. It does not compare against a cheaper standalone single-incumbent collection pipeline.

The revised [protocol](../protocols/LEARNING_SIGNAL_PROTOCOL.md) addresses these issues and keeps unresolved manifest and timing requirements as explicit launch gates. It remains a prospective design. No training improvement or runtime feasibility has been established by this review.
