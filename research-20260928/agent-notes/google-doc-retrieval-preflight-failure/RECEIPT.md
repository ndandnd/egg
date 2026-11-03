# Google Doc receipt — retrieval preflight failure

- Target: original “egg” Google Doc at https://docs.google.com/document/d/1NmPC_qo_uOnA48dV6Ibhs3Pj9EgOD-oJTBuVi41p6bg/edit?tab=t.0
- Exact append source: `research-20260928/retrieval-comparison/failure-attempt1/GOOGLE_DOC_UPDATE.md`; 2,490 bytes; SHA-256 `e5170566cb29458d4279692004bf0b2f812b4edb6c544210ab6e9fe551e96ce0`.
- Appended once at the true end under “Retrieval comparison stopped before optimization — 28 September 2026,” after the existing retrieval-comparison launch update. Existing document history and visuals were preserved.
- The update records Unicorn job 584876 failing in environment preflight before optimization; all 48 planned calls remained unstarted. It records the 12-second allocation, strict platform-mismatch evidence, the repair CI/review, and that no replacement was submitted.
- UI verification: Google Docs showed “Saved to Drive”; the new Heading 2 appeared last in the outline; all four source links rendered as links (“Preserved failure evidence,” “Independent repair review,” “Full repair CI,” and “Concrete replacement decision”). The unique body phrase “All 48 planned solver calls remained unstarted.” was visible.
- Persistence check: reloaded the same document URL once. A targeted find for “All 48 planned solver calls remained unstarted.” returned `1 of 1`, and the new heading remained last in the outline. No export or duplicate append was performed.
