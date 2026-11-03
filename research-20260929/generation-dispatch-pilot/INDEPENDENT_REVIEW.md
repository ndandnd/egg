# Independent algebra check of the three-hour dispatch example

29 September 2026. Read-only review of `paper/latex/dispatch_example.tex` and
this folder's `REVIEW.md`. No new optimization run or manuscript edit.

The timetable requires three consecutive generation hours. With fleet load
`(x,0,30-x)` and background `(0,15,0)`, the middle hour serves background
while service B prevents fleet charging. The stated baseline has cost 75.
Writing A's outputs as `(a,m,z)` makes B's outputs
`(x-a,15-m,30-x-z)` and incremental cost `150+x+a-4z`. For every
`0<=a<=x<=10`, A's two upward ramps and terminal cap give
`z<=min(15,a+10)`. Setting `m=a+5` and `z=min(15,a+10)` attains that bound
without violating either generator's other limits. Minimization over the
whole continuous branch therefore gives `G=110-2x` on `[0,5]` and
`G=95+x` on `[5,10]`. The one-bus cost is 112; the best two-bus cost is
114 at `x=5`.

For a mixture with one-bus weight `λ`, mean early load is
`x=10λ+(1-λ)y`, `0<=y<=10`, so `λ<=x/10`. Cheapest intrinsic cost is
`14-0.7x`, attained at `λ=x/10`. Adding `G` gives slopes `-2.7` and
`+0.3` around `x=5`; hence `CH=110.5` and `D-CH=1.5`. Half of the
one-bus plan and half of the two-bus `y=0` plan realizes the mean
`(5,0,25)`. Its dispatch A=`(5,10,15)`, B=`(0,5,10)` meets both A ramp
equalities, all balances, and capacities.

At that mean, positive interior B output in hours two and three fixes
`p_2=p_3=5`. Let `p_1=s`. A's two binding upward-ramp rents are `7-s`,
its terminal-cap rent is `s-3`, and B's unused early output requires
`s<=6`; nonnegative rents require `s>=3`. These conditions are also
sufficient for a generator dual, so the entire balance-price face is
`(s,5,5)` for `3<=s<=6`. At `s=5.7`, rents `(1.3,1.3,2.7)` have intercept
`5(1.3)+5(1.3)+15(2.7)=53.5`. Because baseline price times demand equals
75, this gives the globally valid incremental cut
`G(L)>=p·L-53.5`. It is tight at the mean. The full fleet oracle gives
`V(p)=164`, so this cut independently proves `CH>=110.5`.

At the physical one-bus load `(10,0,20)`, all B outputs are positive and
interior, fixing the dispatch price at `(6,5,5)`. The plan pays private cost
167, while the zero-early two-bus response costs 164, giving regret 3.
For the two-bus plan at `x=5`, its private cost is `139+5s` and the full
fleet response is `min(107+10s,164)` throughout the admissible face.
Thus regret is `32-5s` up to `s=5.7`, then `5s-25`, with minimum 3.5.
The calculations include every two-bus charge `y∈[0,10]`.

Relaxing only A's two inter-hour upward limits permits `a=0,z=15` for
every fleet load, giving `G_0=90+x`. The two-bus `x=0` plan attains both
the physical and hull minimum 104. All checked manuscript and pilot-review
claims are consistent; no critical mathematical error was found.
