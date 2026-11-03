# Admission-reserve check: one stale regression fixture

24 October 2026. The deliberate source-bound191-case check completed once:
**190 passed, one failed**. Source hashes were unchanged, accounting observations
complete and all three owned groups confirmed absent/reaped with no secondary
cleanup errors. No external freeze, timetable generation or native solve followed.
The failed receipt remains failed in `admission-reserve-checks/attempt01`.

`test_late_serialization_is_censored_and_failure_still_charged` starts its fake
clock at23 seconds, beyond the new planned22-second full-search stop. The
coordinator correctly skips the planner, so the fixture's expected deliberately
raised RuntimeError never occurs. Output still ends at31 seconds and is censored;
the test fails while indexing its empty failure list. This is a stale timing
fixture, not evidence of a runtime deadline/replay failure. Independent review
confirmed the diagnosis without rerunning a test.

The minimal prospective correction is fake start23→21 and serialization8→10.
The planner can then raise before22, and serialization still ends at31. Preserve
all existing assertions: censorship, elapsed31 and the original RuntimeError.
No runtime source, deadline, safety guard or assertion is relaxed. Preserve the
failed source revision in Git before editing. Any deliberate corrected check
needs a fresh source-bound protocol/namespace and all earlier spend carried.

Actual check charge3.0658860423948764s includes the elapsed/child-CPU allocation
maximum plus supervisor CPU. Complete cumulative carry is
**915.958148670185s** in `admission-reserve-checks/accounting.json`, ADMIN0.
Approved1800/1620/180 and one thread/5GiB remain unchanged. Passing fake tests,
when obtained, will not establish actual80-trip timing or native qualification.
