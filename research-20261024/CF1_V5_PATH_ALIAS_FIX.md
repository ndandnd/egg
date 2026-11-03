# CF1 v5 canonical expected owner-root path correction

24 October 2026. The preserved attempt02 source invocation reported one failed,
19 passed and 61 subtests passed in 0.76 seconds. Its sole retained failure is
`OwnerTests.test_owner_fake_process_anchor_argv_ready_and_cleanup_receipt`, at
the full `runtime[-8:]` argv assertion. The actual `--owner-root` used the
canonical `/private/var/.../entry-owner.json`; the handwritten expected path
used the `/var/.../entry-owner.json` alias. The displayed hash, flags, file
descriptor and nonce matched. Assertions later in this method were not reached.

Following closure and preservation of attempt02, the prospective test-only
correction resolves the expected owner-root path before converting it to text.
The full argv equality remains in place. Passing handwritten source receipts
now identify fresh attempt03; mismatched receipt identities identify attempt02,
and the old-directory rejection still identifies attempt01. No production owner
source or guard is changed. No other unobserved behavior is patched.

The parent reports preserved attempt02 closure with 191 snapshot files (9 new,
182 reused), all 1111 proof hashes verified, and cumulative carry
1538.9434496310162 seconds. The separately decided attempt03 source allowance is
8 seconds, with a cumulative endpoint of 1546.9434496310162 seconds, within the
existing wake and phase ceilings. This note grants no additional budget, credit,
retry or invocation authority.

Only this note and the specified path/receipt-identity fields in the new test
source were edited for this correction. Attempts01/02 and their frozen bytes
remain preserved. No imports, tests, native work, data work, cluster work or
commits were performed by this correction. The edit establishes no passing
coverage; any separately frozen source invocation establishes only its actual
source-level results, never real runtime ownership, timing, native entry or the
CF1 mechanism.
