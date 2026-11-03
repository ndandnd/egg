# Integrated manuscript rendering and review

Root compiled main.tex with Tectonic and BibTeX and visually inspected all
19 rendered pages, including all five figures, four tables, mathematical
expressions, proof appendix and references. After the final source-attribution,
citation-order and bibliography-note edits, only pages 2, 3, 8 and 19 changed
in the PNG comparison; root inspected those four again, and the other fifteen
were byte-identical to their reviewed renders. No clipping, overlap, missing
mathematical glyphs or unreadable labels remained. The final log has no TeX
warnings, overfull/underfull boxes, undefined references or missing characters.

The abstract has 149 words. The bibliography cites all seven requested core
sources plus five directly relevant bus scheduling/public-source entries.
The public timetable witness figure explicitly represents original numerical
pilot schedules, separately from the ideal exact witness. No failed-run banner
or qualification history is presented as a headline result. Paid failures remain
in the computational tables and figure. Existing historical PDFs are untouched.

The initial cached build lacked amsthm; root fetched standard TeX dependencies
and subsequent builds used the cache. A separate agent's local build could not
fetch that package; the root's successful compilation is the delivered artifact.
No full solver suite was rerun for manuscript-only changes. Latest prior backup
CI36479784860 passed. Core textual mathematics and literature boundaries have a
separate bounded independent review; the archived flat-objective reconciliation
has an independent review and changes no original experimental status.
