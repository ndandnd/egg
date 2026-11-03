# Local execution log and superseded result handling

The first two-period command (`PYTHONPATH=src python3 .../run_pilot.py`) returned
success in a tool-reported **0.31548675 s** wall time, before the omitted
`[2,3]` hour was identified. Its output then lived at `RESULT.json`. The
three-period correction reran the same path and overwrote that JSON; the
original JSON file is **not retained**, and no later file should be called an
original copy. The initial output visible in the tool receipt had ramped
incremental costs 110, 100, 105 at x=0,5,10 and hull 110.5, but those figures
are preliminary algebra checks only. [PROTOCOL.md](PROTOCOL.md) preserves the
original two-period declaration and the pre-solve chronology amendment.

The corrected three-period run first returned success in **0.355537792 s**
tool wall time, and a later repeat after the explicit HiGHS thread/time cap
returned success in **0.124699334 s** tool wall time. The latter wrote the
currently retained [RESULT.json](RESULT.json), with the three-hour demand,
background subtraction, and ramp constraints. Those timings come from command
receipts, include process startup and serialization, and are not solver speed
measurements. The retained JSON predates per-LP instrumentation and contains no
individual LP times; none are reconstructed.

Focused tests first failed on a nested `pytest.approx` assertion after **0.605857625 s**
tool wall time, then passed 2/2 after the assertion was fixed (**0.467304083 s**).
After the explicit native-thread cap, the same two tests passed again in
**0.500127375 s**. The Fraction certificate passed before and after the
chronology change; the corrected certificate passed after the 3-hour run.

The runner now creates a timestamped result by default, or accepts `--output`
for a chosen **new** path, always using exclusive creation. Future outputs
record total process wall time and each underlying tiny HiGHS LP wall time.
Every LP requests one HiGHS native thread and has a ten-second solve limit.
