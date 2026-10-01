# Six-cell cold-hull baseline viability screen

All six declared cells returned on time with replayed native global
enclosures. The three **target-market** cells certified after 2, 2 and 3
pricing calls for 8, 16 and 24 services. All three **flat source-market**
cells stopped on projected rational-bit growth after 3, 4 and 5 calls,
respectively, leaving global widths of at most 0.347382, 0.181109 and
0.053880 cost units. Thus the 16-call budget was not the observed barrier
in this development family. The source-market arithmetic stop remains a
configuration issue before a fair cold/retained/nearest-neighbor comparison.

| Services | Market | Outcome | Calls / masters | Max bits | Native global interval | Width ≤ | Child s | Pricing s | Polish s |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | Flat source | Bit-limit stop | 3 / 3 | 8025 | [444.7930, 445.1405] | 0.347382 | 3.94 | 0.21 | 1.60 |
| 8 | Shifted target | Certified | 2 / 1 | 160 | [427.9219, 427.9220] | 0.000002 | 2.23 | 0.04 | 0.005 |
| 16 | Flat source | Bit-limit stop | 4 / 4 | 7978 | [488.7192, 488.9004] | 0.181109 | 11.71 | 3.75 | 4.77 |
| 16 | Shifted target | Certified | 2 / 1 | 167 | [471.1218, 471.1219] | 0.000002 | 4.69 | 2.35 | 0.004 |
| 24 | Flat source | Bit-limit stop | 5 / 5 | 8186 | [539.2309, 539.2849] | 0.053880 | 50.87 | 35.43 | 9.15 |
| 24 | Shifted target | Certified | 3 / 2 | 169 | [542.3015, 542.3016] | 0.000002 | 20.61 | 16.40 | 0.008 |

The lower endpoint rounds **down**, the upper **up** to four decimals;
widths round **up** to six. The certified stored-number widths are about
`1e-6`, within the configured `1e-4` criterion. A projected bit-size stop
need not have an observed maximum above 8192: the maxima here are 8025,
7978 and 8186. These fraction-valued native results retain solver and
physical-replay tolerances. They are not exact ideal-model proofs.

Polishing is the larger **recorded** component in flat-source cells at 8
services (1.60 versus 0.21 s pricing) and 16 services (4.77 versus 3.75 s).
At 24 services native pricing is larger (35.43 versus 9.15 s polishing).
Pricing is also larger than polishing in each target cell, especially at
16 and 24 services. Recorded restricted-master native time ranges from
0.002 to 0.013 s per cell. These components do **not** exhaust child wall
time: cold model construction and other preparation are not separately timed,
so the residual cannot be assigned to any one operation. The complete
[CSV](compactrows.csv) and [JSON](compactrows.json) preserve every scalar
component and SHA-256 hashes of the sealed exact-fraction endpoints.

The six child wall times total **94.05 s**. The supervisor records **96.61 s**;
the wrapper records **14 s** setup and **112 s** whole-wrapper elapsed.
[Slurm accounting](sacct.txt) records **114 s** for job 593482 on one CPU,
with exit `0:0`; these clocks have different boundaries and should not be
added. No child failed or hit its 210 s hard cap. Freeze, preflight and
supervision returned zero, with unchanged source hashes and a quiescent seal.
All six cells use nested sizes from one synthetic seed-1006 development
family, with one native GRB seed 0. They do not measure variability,
cross-timetable transfer or comparative acceleration.

**Next bounded diagnosis.** Run the *same six cells* in a fresh, separately
frozen development attempt with the existing numerical-QP restricted-master
proposal. Keep the physical cases, both markets, compact GRB pricing, seed 0,
one thread, 16 calls, 8192 bits, 64 master/pool headroom, 10 s reserve,
160 s native phase, 180 s coordinator wall and 210 s hard child cap. Use the
existing fixed-denominator proposal controls (`10^9`, maximum 500
iterations); change only the master policy. Preserve all stops and compare
on-time global enclosure quality, calls, recorded component time and full
child time to this baseline, without calling a single-run time difference a
speedup. The same six-child 1500/1600/1800 s controller/outer/Slurm ceilings
bound the attempt. This tests whether the current arithmetic stopping barrier
is avoided before designing a larger retained/nearest-neighbor study. It
does not imply that the master dominates runtime: native pricing is the
largest measured component at 24 services, so route proposals may still help.
The diagnosis does not retry or change the old frozen retrieval protocol.

The [summary-only script](summarize.py) reproduces the compact rows from
the sealed summary, declaration, supervisor/wrapper receipts and six
receipt/assessment pairs. It does not inspect event logs or invoke a solver.
Execution source commit: `e3ac75fc53c00594572126413b704ab1de42086e`.
