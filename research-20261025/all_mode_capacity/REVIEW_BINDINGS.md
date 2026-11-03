# Parent binding and integration review

Static review only. No artifact/spec values, imports, compilation, tests or hashes
were read/run. Reviewed the new caller and only the necessary existing writer
and physical dataclass schema sections.

The resource-recourse task writer assigns the four p90 acquisitions to ordinals
1/4/5/8 and task IDs A001-g10001-p90, A004-g10006-p90,
A005-g10009-p90 and A008-g10005-p90. Its external record inherits task context,
literal folder and the SHA256 of the serialized spec buffer. The spec writer
stores root/context, fixed fleet_N, expected_case_identity and asdict(case).
The new caller's literal paths and permitted projection match that contract.
No old receipt status or objective is needed. The existing worker validated the
full case identity and physical schema; that provenance is inherited, rather
than recomputed with forbidden cost fields.

The new projection retains the NativeCase/Trip/Movement/Leg/Resource physical
fields required for the declared cut. It deliberately does not read costs,
prices, selected movement IDs, plans, cached replay, charges or loads. Whole JSON
decode is explicitly transient, followed by projection and discard. Source
bytes, protocol/manifest and the eight admitted input buffers are hashed once
inside the metered process, with no shell hash audit.

Parent requested narrow prelaunch additions: explicit trip-count agreement,
recorded inherited identity token, permitted failure reason, observed self
high-water RSS reporting/check and an explicit binary-coefficient arithmetic
convention. Independent mathematical review is recorded separately in REVIEW.md.
These changes do not expand the input scope or scientific question.

Funding is a separate NEW 30 CPU/60 wall package, not a reopening of the closed
20/45 or 4500/7200 packages. Retained prefix 19811.37 CPU seconds remains a
tracking sum, not exact session CPU; the separate legacy guard and unknown actual
old review CPU remain unchanged. Prepublication observations exclude final write
and exit, which the external meter must close. No native worker or child exists.

Any negative ideal cut for a known replay-admitted control (all p90 controls,
10001/p45 and 10006/p45) is a discrepancy requiring diagnosis. Passing cuts leave
the unresolved fixed-N cases unresolved; they are not feasibility witnesses.
No source tests, native retries, fleet changes or training follow automatically.

Disposition: PASS. The requested narrow additions are present, and the independent
review passed before commit/dispatch. The exact new allowance/command is frozen
in LAUNCH.json and PROTOCOL.md; neither review itself is execution.
