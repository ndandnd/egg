# Draft 0.9 release check — 29 September 2026

Artifact: `output/pdf/egg-journal-v0.9-reviewed-draft.pdf` (21 pages).
SHA256: `2ebc975349eaf452ff285d8c66e7ba81e548243dd82adcf1c22c2abb3ca0133f`.

## Verified scope

- Two focused dispatch tests pass, including balance, binding hourly ramps,
  primal/dual equality, the price face, the relaxed-ramp control and infeasibility.
- Fraction-based certificate passes. Sol independently checked the full continuous
  charging branch, hull lower bound, price face, both regrets and relaxed control.
- Sol independently recomputed all 20,000 analytic trace rows and verified the
  oracle, update, conjugate, current/best bounds and response-frequency counters.
- Luna verified source attribution against available primary sources. Hreinsson's
  public abstract and metadata support the aggregation context; its full theorem
  statements were not available for verification. EGG rates are proved separately.
- Tectonic completed with no overfull/underfull or undefined-reference warnings.
  All 21 pages were rendered and inspected in page montages; new figure assets
  and final pages 10–12 and 16 were also inspected at readable resolution.
  The final evidence-map update leaves pagination at 21 pages.
- Figures distinguish current versus best dual values and physical versus hull
  costs. The hourly example includes the intervening service/background hour.
- Public results are unchanged. The release does not claim a public positive gap,
  timetable speedup, unique-price convergence or universal schedule nonconvergence.

## Execution limitations and failures retained

`generation-dispatch-pilot/RUN_LOG.md` records the superseded two-period attempt,
its overwritten JSON and all known pilot/test wall receipts. No original lost
receipt is reconstructed. Per-LP timers were added prospectively; historical
LP times are not inferred. Root's initial test invocation omitted `PYTHONPATH`
and failed during collection in 0.135125375 s, before solving. The corrected
invocation passed 2/2 (0.38 s pytest; 0.476859667 s command wall). After the
prospective timing helper, the final 2/2 check took 0.50 s pytest and
0.686976292 s command wall; the Fraction certificate also passed. These are
validation times, not performance claims. An initial authoring/build invocation
used the wrong directory and failed before editing/building; the corrected
working-directory build succeeded. No cluster job, native fleet solve,
protected outcome or reset credit was used.

This is a focused theory/example release ready for author review, not a claim
that the broader computational journal-paper objective has been completed.
