#!/usr/bin/env python3
"""Bibliography tooling for ref/papers.csv.

Usage (from the repository root or ref/):
    python3 ref/tools/bibliography.py validate
    python3 ref/tools/bibliography.py gen-index

`validate` checks: header schema, unique keys, unique normalized identifiers
(DOI/arXiv aliases unified), enum fields, and that every audited-full-text row
carries local_files. Exits nonzero on any violation.

`gen-index` regenerates ref/LITERATURE_INDEX.md from ref/papers.csv.
papers.csv is the master; never hand-edit the index.
"""
import csv, re, sys, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.dirname(HERE)
CSV_PATH = os.path.join(REF, "papers.csv")
INDEX_PATH = os.path.join(REF, "LITERATURE_INDEX.md")

COLS = ["key","authors","year","title","venue","identifier","evidence_tier",
        "relevance","documented_in","local_files","notes"]
TIERS = {"audited-full-text","abstract-level","institutional/grey"}
RELS = {"core-threat","method-anchor","domain-context","deprioritized"}

def norm_id(s):
    """Normalize an identifier: lowercase, strip DOI prefixes and spaces,
    unify arXiv forms (arXiv:X == arXiv X == 10.48550/arxiv.X). Only the
    first identifier is used when several are listed with ';'."""
    s = (s or "").split(";")[0].strip().lower()
    s = re.sub(r"^(doi:\s*|https?://doi\.org/)", "", s).strip()
    m = re.match(r"^(?:arxiv[:\s]+|10\.48550/arxiv\.)(\d{4}\.\d{4,5})(v\d+)?$", s)
    if m:
        return "arxiv:" + m.group(1)
    return s.replace(" ", "")

def read_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        if rdr.fieldnames != COLS:
            sys.exit(f"FAIL header: {rdr.fieldnames}")
        return [{c: (r.get(c) or "").strip() for c in COLS} for r in rdr]

def validate():
    rows = read_rows()
    errs = []
    keys = Counter(r["key"] for r in rows)
    for k, n in keys.items():
        if n > 1: errs.append(f"duplicate key: {k}")
        if not k: errs.append("empty key present")
    ids = {}
    for r in rows:
        i = norm_id(r["identifier"])
        if i:
            if i in ids:
                errs.append(f"duplicate identifier {i}: {ids[i]} vs {r['key']}")
            ids[i] = r["key"]
    for r in rows:
        if r["evidence_tier"] not in TIERS:
            errs.append(f"{r['key']}: bad tier {r['evidence_tier']!r}")
        if r["relevance"] not in RELS:
            errs.append(f"{r['key']}: bad relevance {r['relevance']!r}")
        if r["evidence_tier"] == "audited-full-text" and not r["local_files"]:
            errs.append(f"{r['key']}: audited but no local_files")
        if not r["documented_in"]:
            errs.append(f"{r['key']}: empty documented_in")
    aud = sum(1 for r in rows if r["evidence_tier"] == "audited-full-text")
    if errs:
        print("\n".join(errs)); sys.exit(f"FAIL: {len(errs)} problems, {len(rows)} rows")
    print(f"OK: {len(rows)} rows, {aud} audited, "
          f"tiers={dict(Counter(r['evidence_tier'] for r in rows))}, "
          f"relevance={dict(Counter(r['relevance'] for r in rows))}")

def line(r):
    a = r["authors"] or "(authors not captured)"
    if len(a) > 60: a = a.split(",")[0].strip() + " et al."
    y = f" ({r['year']})" if r["year"] else ""
    t = f" *{r['title']}*." if r["title"] else " (title not captured)."
    v = f" {r['venue']}." if r["venue"] else ""
    i = f" `{r['identifier']}`." if r["identifier"] else ""
    g = " [grey]" if r["evidence_tier"] == "institutional/grey" else ""
    n = f" — {r['notes']}" if r["notes"] else ""
    return f"- `{r['key']}`{g} — {a}{y}.{t}{v}{i}{n}"

HEADER = """# Literature index

Generated from `papers.csv` by `tools/bibliography.py gen-index` — regenerate,
do not hand-edit. `papers.csv` is an *encounter ledger*: one row per unique
work encountered during the review, with metadata copied verbatim from the
source notes (never fabricated); many abstract-level rows are intentionally
incomplete and are completed opportunistically when a paper is audited.

Evidence tiers: `audited-full-text` = the 17 supplied papers with paper-level
notes in `review_notes/`; `abstract-level` = found by web scans, verify full
text before citing details; `[grey]` = institutional/grey literature (reports,
theses, market descriptions, working papers, course notes).

Relevance classes: core-threat (named novelty threat), method-anchor
(foundation we build on), domain-context (nearby applied work). Per-paper
discussion locations are in the `documented_in` column of `papers.csv`;
detailed notes live in `review_notes/` and `review_notes/agents/`.

"""

def gen_index():
    rows = sorted(read_rows(), key=lambda r: r["key"])
    sections = [
        ("1. Audited full text (17 supplied papers)",
         lambda r: r["evidence_tier"] == "audited-full-text"),
        ("2. Core novelty threats (abstract-level; verify before citing)",
         lambda r: r["evidence_tier"] != "audited-full-text" and r["relevance"] == "core-threat"),
        ("3. Method anchors",
         lambda r: r["evidence_tier"] != "audited-full-text" and r["relevance"] == "method-anchor"),
        ("4. Domain context",
         lambda r: r["evidence_tier"] != "audited-full-text" and r["relevance"] == "domain-context"),
        ("5. Deprioritized",
         lambda r: r["evidence_tier"] != "audited-full-text" and r["relevance"] == "deprioritized"),
    ]
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(HEADER)
        for title, pred in sections:
            sel = [r for r in rows if pred(r)]
            if not sel: continue
            f.write(f"## {title} ({len(sel)})\n\n")
            for r in sel: f.write(line(r) + "\n")
            f.write("\n")
        f.write("## Appendix: local source files for audited papers (under `papers/`)\n\n")
        for r in rows:
            if r["evidence_tier"] == "audited-full-text" and r["local_files"]:
                f.write(f"- `{r['key']}`: {r['local_files']}\n")
    print(f"wrote {INDEX_PATH}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "validate": validate()
    elif cmd == "gen-index": gen_index()
    else: sys.exit(__doc__)
