# Bounded independent diagnosis

GPT-6.1 Sol, read-only after native completion; no code edits, imports, tests,
solver/cluster calls, raw-log/capture dump or retry. Root separately ran the saved
independent analyzer.

CF1 first_completion_anchor=t0+2.2039999589. Deadline=min(t0+12,first+6)=
t0+8.2039999589. Provider return=t0+20.3918937091. Construction made50 merges and
30 optimistic routes. Therefore pre-provider setup+construction consumed at
most2.204s; the overrun is in preparation before the first fixed inventory/native
CF1 dispatch, not in the CF1 optimizer. A native_model60 event precedes that
missing inventory, but has no timestamp; exact substage attribution is unavailable.

The charging helper performs two full _inventory scans, including physical row
signature traversal and repeatedly constructing set(mapped) per variable. These
are cost candidates, not measured exclusive causes. The provider checks lateness
before retaining helper stages/failures, losing the detailed inventory/build
failure. Repair the repeated work, cooperative deadlines and diagnostic retention
under a fresh prospective source-bound protocol. Keep all physical checks and the
same endpoint; a timely valid CF1 witness is not guaranteed by this diagnosis.

The3386.201202 bill is the cold full fallback. Its timely57.0751s endpoint does
not qualify an unexercised CF1 path. Recovery was correctly left undispatched.
