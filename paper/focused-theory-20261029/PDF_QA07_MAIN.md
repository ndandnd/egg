# PDF07 main and early appendix visual review

Parent inspected every actual PNG page1–16, after the once-only compile/render.
No page clipping, overlap, missing glyph or unreadable formula was found in
these pages. Main argument occupies pages1–8; detailed appendix starts on8.
The formal complete projection and short constructive proof are legible.
Two-law public bounds and explicit limitations are clear. No scientific
computation or certificate replay occurred. Tool/visual CPU UNKNOWN.

Specific new-source polish before a separately frozen final snapshot:
- Page12 has stale prose saying framework Section3 used nonnegative loads.
  Framework now explicitly uses signed net loads; replace that cross-reference
  wording without changing the V2G model or formulas.
- Page6/7 splits the optional inline directional-occupancy formula across a
  page boundary. Refer to weighted occupancy in prose; detailed formula is in
  its corollary.
- Put a clear page boundary before the appendix to distinguish the8-page main
  narrative from supporting detail.
- Page3 related-work paragraph has a minor right-margin overhang matching the
  6.77pt log warning. Rephrase the long joint-projection sentence.

Separate appendix reviewer found a visible right-margin overhang on60 and an
awkward heading split on51. See PDF_QA07_APPENDIX. No old output will be
overwritten or rerendered; a new source/control/version is required.
