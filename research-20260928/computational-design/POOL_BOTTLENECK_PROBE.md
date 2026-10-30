# Offline restricted-pool probe

This exploratory post-run calculation used the three saved complete-fleet columns in `result/sistig_nonlinear/20260927-attempt2/hull/result.json`. It reads the paired `frozen.json` and `result.json` only; it does not read event JSONL, launch a native/MIP solver, or change the preserved attempt. The frozen market is `sistig-depot15-30h-high-curvature`, with F(L) = sum_t(a_t L_t + b_t L_t^2/2). Source commit `e23a653dcd77b6ce02eb0af5e544fea7edab9eca`, frozen SHA-256 `eb1d9f5dc8b8f7f1561c21dd8f8cad6105f8cfbc272c23b8c8a334e6a626f352`, case identity `1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7`, market identity `5d332a628b4713e96705e468a4526b4d7c650007492152b431b8709e6d006b64`, and extraction policy `native-pathflow-orphan-projection-v1` matched. All three complete-fleet plans replayed under that policy.

SciPy 1.13.1 SLSQP minimized the quadratic over the simplex of those three columns, using an analytic gradient and five deterministic starts. It proposed weights about `[0.320948802, 0.299156549, 0.379894649]`. The objective was 454.69384112501353 versus 454.6938411610447 for the archived mixture, a decrease of only 3.60e-8. The simplex directional first-order residual fell from 0.00201892 for the saved mixture to 1.22e-9 for the numeric proposal.

The proposal was rounded to integer units with denominator 1e9; the largest component absorbed the integer-unit correction, making the rational weights sum exactly to one. The existing exact mixture replay and restricted-pool Fenchel check accepted those weights at the same extraction policy. The restricted three-column pool gap was 7.23e-8, versus 0.00201892 for the saved mixture. This is a local pool diagnostic: the pool Fenchel lower bound is valid for these three columns at the reported price, but no fresh full-fleet pricing call was made. It says nothing about omitted columns or the global hull gap. The exact replay helper emits a fixed internal `exact-pairwise-polish` source label; these proposal weights came from SLSQP followed by fixed-denominator rounding, and no pairwise polish was run.

Measured on the local machine: initial column replay 0.078 s; exact replay and pool check of the saved mixture 0.070 s; five SLSQP starts 0.0025 s; exact replay and pool check of the proposed mixture 0.069 s; total probe function 0.244 s, excluding interpreter import and output-file writing. These separate stage timings do not compare against a full-solver run. This suggests a cheap restricted-pool candidate generator for separate design review, not a full-solver speedup. The archived attempt remains `budget_exhausted`; its independent strict polishing-cap violation is unchanged and is not cured by this offline calculation.

Reproduce from the repository root with:

```sh
python3 research-20260928/computational-design/pool_bottleneck_probe.py
```

Inputs: frozen SHA-256 `eb1d9f5dc8b8f7f1561c21dd8f8cad6105f8cfbc272c23b8c8a334e6a626f352`; hull `result.json` SHA-256 `bad0a1530f43ba00f6afccfe4272d590eb5649c2679b6d6c7ac6daf51cbfe0a6`. Probe script SHA-256 `f4f56b62df46f72ff725a96d9d93d70cc2f30ead4c55ddfb69f3733d1f83648c`; output SHA-256 `b945701ed829a788e1c27d0e119a1f2c7b0b55103ad5f9149c1052e0719253c8`.
