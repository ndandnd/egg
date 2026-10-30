## Testing the stopping limits — 28 September 2026

A controlled eight-cell diagnostic has been submitted to Unicorn to test why cold iterative solving stopped early on the three-service example. It crosses four versus sixteen pricing calls with 4096 versus 8192 arithmetic bits, independently in the original and changed markets. Other solver controls stay fixed, and every run starts without retained plans or inherited bounds.

The earlier runs hit different limits in the two markets. This experiment will distinguish the effects of those limits and identify any new limiting step. It does not assume that sixteen calls will certify the case, and it will retain failures and all spent time. It is a development diagnostic, not evidence of scalability or a general speedup.

Sol implemented the runner, Luna reviewed it, and the focused checks and full hosted test suite passed. One serial job requests one CPU and 8 GB for at most 20 minutes; it has no automatic retry. The failed retrieval comparison and its pending replacement decision remain separate. The current manuscript stays at draft 0.7 while computational work continues.

[Diagnostic design and independent review](https://github.com/ndandnd/egg/tree/1dba007ee4868f0d29373a84b7880171ab3c358c/research-20260928/budget-sizing-diagnostic)
