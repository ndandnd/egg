# Independent arithmetic and scope review

Reviewed only the parent-provided incident description. No commands, source
imports, hash checks, qualification, data access or native execution were run
for this review. Prior roots remain immutable.

The arithmetic is consistent:

- Review02: (49.347 + 2) s × 10 single-thread process slots = 513.470 CPU-s.
- Review03: (32.931 + 2) s × 10 slots = 349.310 CPU-s.
- Guarded review charge: 862.780 CPU-s; with 25 s incident/handoff/verification
  closure, the additional conservative charge is 887.780 CPU-s.
- Prior 1538.9434496310162 + 887.780 gives approximately
  2426.7234496310164 CPU-s (last-digit floating-point rounding).

This is a sensible conservative reconciliation **conditional on** the stated
upper bound of five simultaneous single-thread shell/jq/shasum process slots
per loop, two concurrent loops, loop execution contained within the recovered
windows plus each 2 s guard, and the 25 s allowance covering all additional
incident closure work. Charging every slot throughout both entire windows also
charges LLM/idle time and avoids relying on unknown polling gaps.

Actual CPU, process occupancy, monitoring gaps and peak RSS remain unknown.
Neither a measured process census nor measured CPU validates the slot bound;
the bound rests on the supplied trusted-utility process structure and
single-thread assumptions. The timestamp guards and closure allowance are
conservative assumptions, not measured usage or unconditional proof. Any work
outside those bounds requires additional reconciliation. Do not describe this
guard as exact usage or claim that prior source/global caps were respected.

The guarded carry exceeds the prior 1920 s ceiling, 1740 s dispatch stop and
1702.8351450899538 campaign end. Prior source-cap compliance also cannot be
claimed. Stop qualification and native work. Prepared attempt03 is cancelled
unsubmitted, not a failed execution or a retry; its prepared artifacts remain
frozen. No native worker has been launched according to the supplied account.

The proposed new 3000 s total / 2820 s dispatch / 180 s shutdown policy is
arithmetically coherent: one fresh 175 s package would end at approximately
2601.7234496310164, leaving 218.2765503689836 s before dispatch stop and preserving
the full 180 s shutdown reserve. This proposal requires explicit human approval
of the new 50 CPU-minute total; prior approval of 32 minutes does not authorize
it. Scope remains only the 40-case CF1 seed17/day/no-fault experiment.

After any approval, batch hashing belongs only inside existing metered Python
preflight/finalization. Peer review should inspect static fields and avoid
duplicate external hash loops. No future execution is authorized by this note.
