"""Render current display equations without regenerating scientific figures."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'paper/manuscript.md'
OUT = ROOT / 'paper/figures'
plt.rcParams.update({'font.family': 'DejaVu Sans'})
rows = []
for number, line in enumerate(
        [s.strip() for s in SOURCE.read_text().splitlines() if s.startswith('$$')], 1):
    assert line.endswith('$$')
    target = OUT / f'equation_{number:02}.png'
    fig = plt.figure(figsize=(7, .34))
    fig.text(.5, .5, '$' + line[2:-2] + '$', ha='center', va='center', fontsize=13)
    fig.savefig(target, dpi=300, bbox_inches='tight', pad_inches=.05, facecolor='white')
    plt.close(fig)
    rows.append({'number': number, 'source': line,
                 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
(OUT / 'equation_provenance.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'matplotlib': matplotlib.__version__, 'equations': rows}, indent=2) + '\n')
print(f'Rendered {len(rows)} current equations')
