# Fixed-topology attempt01: closed, exact public recovery unresolved

Source `3278d50f8323618bd36809b1bbb1a0da081e23ff`; control `4a5b19a0` (parent-supplied provenance). Owner 62232 exited zero; worker 47427 exited zero and was reaped. Administrative status CLOSED does not denote successful public exact recovery.

| Assigned state | Delivered outcome |
|---|---|
| Q0 | PASS: native status 2 and exact fixed-topology objective/lower equality at `41633276555247252423/4611686018427387904` |
| FIXED_QP_RECOVERY | Native status 2, objective 441.53291205116824; exact RECOVERY_FAILED at ALL_COORDINATE_BOX_CERTIFICATE: recovered multiplier has wrong sign |
| OWN_PRICE_LP | UNATTEMPTED: exact physical recovery prerequisite not met |
| OWN_PRICE_MIP | UNATTEMPTED: same prerequisite |

Q0 matches the declared exact binary-coefficient value `7+10*a+25*b`. Public recovery supplies neither an exact objective nor an exact lower certificate. No new public physical upper, global optimum or price-support result was established. No topology or instance infeasibility follows.

The complete compact ledger, receipts and external meter agree on closure, no failure exception and resource pass. External cost is **1.35 CPU seconds** (1.19 user + 0.16 sys), **1.47 wall seconds**, retained **1.37 CPU seconds**. Worker/owner observations overlap and are not additive. Separate artifact-runtime costs are excluded here; parent maintains the combined account.

Review used compact results/receipts and external meter only; no gzip, replay, native execution, tests or hashes.
