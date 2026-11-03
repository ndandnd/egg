# Independent source-only integration review

Read producer.py, extractor.py, worker.py, run.py, PROTOCOL.md and FIELD_AUTHORITY.md once, with narrow producer-delta follow-up. No actual public metadata, scientific packet, import, execution, test, hash, native call or commit. This note is static review, not a passed qualification.

**Code-path verdict: scoped PASS for the metadata-only exact OD gate. One protocol numeric-semantics wording correction was requested from parent before freeze.** The independent checker was authored separately and never calls producer/extractor. Its new literal_qualification uses its own hand-fixed complete PASS/FAIL summaries, plus corrupted counts/minima/witness/false-PASS and malformed-input controls; these are unexecuted.

## Producer and independent agreement

Producer and checker each reconstruct both matrices and evaluate all ordered source-index triples, including repetitions. Scientific schemas align: l² entry counters, l³ prospective/attempted triangle counters, exact minima, negative/diagonal counts, violation counts and first20 typed witnesses per metric. Slack is M[i,k]+M[k,j]−M[i,j]. Nonnegative/diagonal failures do not short-circuit triangles. Producer's distance-only/time-only control now explicitly checks the opposite metric's zero violation count; its earlier conditional-expression precedence error was corrected in new source before freeze.

The independent checker requires exact five-key projection, bounded typed IDs/no mixed aliases, complete unique entries, exact integer/rational-string quantities, size/bit limits and units. It compares all scientific fields, with strict witness types so bool indices cannot equal integer indices. A matching metric FAIL returns FAIL with summary_matches=true: this is an admitted gate failure, not a failed independent implementation. Worker correctly admits scientific PASS or FAIL only with summary_matches=true and matching metric_status. UNKNOWN cannot advance to a theorem claim.

## Extractor and input authority

The extractor accesses only shared location order, OD fields and stop/depot flags from one admitted source buffer; it does not select native_cases or service/movement rows. Required source-ID row-major order, full pair denominator, units, nonnegative source values and integral/half-minute time lattice are explicit. Extra extractor provenance is kept separate; worker projects only the five algorithmic keys. The worker reads the fixed committed buffer once, checks exact recorded length/SHA, rejects duplicate JSON keys/nonfinite constants and uses parse_float=str/parse_int=int. It does not follow metadata paths or silently repair/close a matrix. Paired physical path realizability is explicitly UNKNOWN.

The numeric property certified is exact rational arithmetic on retained JSON decimal tokens, not on a newly inferred original MATLAB float and not an energy-rounding audit. **Requested protocol fix:** replace the contradictory sentence requiring Fraction(original_float) transfer with the actual decimal-token contract already stated in FIELD_AUTHORITY. Accepting a metric under one representation does not establish energy dominance under another.

## Worker, owner and limits

Four assigned states are fixed; failures preserve FAILED/UNATTEMPTED closure, and missing/malformed master gives owner UNKNOWN_UNREPORTED states. Frozen source/control, exact namespace, source-buffer admission, fixed input identity, no-site/isolated stdlib invocation and zero native-call declaration are checked. Parent owns launch authority. Source/RSS/time observations, output serialization, complete owner master read and cleanup are paid under the external package meter. A checkpoint is not a guarantee that an individual Python loop is asynchronously interrupted: the owner/process limits supply that separate boundary.

The source declares package720CPU/900wall and worker660CPU/840wall; worker emergency RLIMIT_CPU620 is deliberately tighter than its acceptance ceiling. This can stop work before nominal acceptance limits, but cannot manufacture a PASS. Owner timeout/kill/wait and final receipts separate complete administrative closure from metric status.

On every result, mode coverage, charging access, energy dominance and physical canonicalization remain UNATTEMPTED/NOT_ESTABLISHED. A triangle failure blocks this chosen sufficient-proof route; it does not prove an improving path exists, that price support returns, or that the existing declared-graph positive-gap certificate fails. No matrix outcome is predicted here.

## Final narrow prefreeze delta: PASS

Narrow source inspection confirms PROTOCOL now explicitly specifies parse_float=str/parse_int=int and Fraction(encoded decimal token), not Fraction(float(token)); the separate upstream/downstream binary-energy bridge remains UNATTEMPTED. Producer and independent checker both bound an exponential token to256 characters and check the exponent's absolute integer value<=1000 before Fraction construction. The independent guard no longer rejects harmless leading zeros solely by exponent digit count. Input rational-bit and arithmetic ceilings remain in place. The prior wording/compatibility hold is resolved; scoped static integration PASS, with runtime literal qualification and parent freeze still separate. No test, import, hash or data read was performed.

## Subsequent extractor property/admission separation: PASS

Narrow source read confirms project_od now only validates finite bounded numeric representation before retaining each original OD token. It no longer rejects negative quantities, fractional seconds or values off the half-minute lattice. This **supersedes the earlier extractor paragraph's nonnegative/integer/lattice claim**: those physical-timing gates were inappropriate prerequisites to a complete matrix-property test and could mask a reportable metric FAIL. Producer and independent checker receive such finite data and still perform all entry/diagonal/triangle checks; fractions are not themselves a metric violation. FIELD_AUTHORITY now explicitly states this distinction and leaves physical timing/energy qualification outside scope. The numeric size/schema guards remain intact. Source-only delta PASS; no full re-audit, execution or actual data read.
