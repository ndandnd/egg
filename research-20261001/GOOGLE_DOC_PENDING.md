# Pending Google Doc updates (append in order to the research log)

The research log is https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg/edit.
This session has only the Google Drive connector (read/create), not the Google Docs
editor, so these updates cannot be appended in place yet. Once the Docs connector is
enabled they will be appended verbatim; until then this file is the record.

---

## Claude takeover — 1 October 2026

Codex schedules are paused. Claude (Opus 5.5) is running the research for about 1.5
days on branch `claude/research-20261001` (independent of the Codex branch).

**Assessment.** The theory is correct and is the strongest contribution. The learning
campaign had three gaps: no matched-wall-time comparison with cold solving; training
where cold solving is already fast (20-28 trips); and no price-support evidence,
because all 32 v7 hull controls failed on a keyword typo. Full text:
`doc/CLAUDE_ASSESSMENT_20261001.md`.

**v8 longer training (collected).** Graph attention trained up to 900 epochs reproduces
the v6 300-epoch anchor exactly and improves held-out ranking substantially: log loss
0.0543 vs 0.0719, average precision 0.899 vs 0.843, top-k recall 0.764 vs 0.740. It
now beats every tree model. Most runs were still improving at epoch 900.

**E1, topology vs tariff (saved v7 data).** Across 16 timetables, the bus count never
changes with the tariff, but the route topology changes in 14/16: under the midday-
cheap tariff the solver adds depot visits and doubles midday charging. This explains
the v7 learned-route loss: training labels come from only two (flat and evening-cheap)
tariffs.
