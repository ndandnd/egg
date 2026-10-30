# Independent review: manuscript 0.3 public case and Figure 6

Review date: 2026-09-27. Scope: manuscript §8, Figure 6 and its source/provenance, checked against `doc/SISTIG_PUBLIC_CASE_PROTOCOL_20260927.md`, `data/public/sistig_26088190_v1/hildenbrand_native_cases.json`, the attribution file, and figure provenance. No manuscript or figure edits made.

## Finding

The main public-case claims and reported numbers are supported. The derived input contains 37 unique Hildenbrand services, split 19/18 across routes 967/968; the selected-day offset is retained through the final 24:24 arrival. The 5×5 source-ordered matrix is directed, and the source's half-minute DHD times are preserved. The two 37-bus constructive references replay successfully without a solver. Their source-JSON energy totals are 2,089.8764409985943 kWh (depot 15) and 2,769.8144794193886 kWh (depot 16); the manuscript's 2,089.876 and 2,769.814 values are consistent. Figure provenance hashes for its JSON, script, PNG, PDF, and SVG all verify. The caption correctly marks energy as modeled, references as replay-checked and non-optimized, and the two depot variants as separate scenarios. References [13] and [14] identify the 2025 article and version-1 Figshare dataset; the local attribution record includes the CC BY 4.0 attribution and adaptation notice.

## Corrections recommended before freezing 0.3

1. **Stale status (§8, line 189):** “Separately declared one-depot, single-connector scenarios remain under preparation” is contradicted by the next paragraph and Figure 6, which report prepared variants and replay-checked witnesses. Replace with a status limited to remaining work, such as “The two one-depot, single-connector variants have passed preflight; a pricing or hull qualification remains.”
2. **Energy language (§8, line 191):** “expensive repeated pullouts and returns” can read as a monetary-cost claim, but the plotted and reported quantity is modeled energy and no cost is calibrated. Prefer a factual description such as “each reference includes one modeled pullout and pull-in per service.”
3. **Battery wording (Figure 6 caption, line 195):** “full battery inventory” could be read as the 600 kWh installed-battery reference. The modeled usable inventory is 400 kWh. Say “full 400 kWh usable inventory”; “Each variant restores…” would also make clear that each separate scenario has its own one-connector assumption.

These are status/precision edits, not failures of the source extraction or arithmetic. Retain the existing qualifications that the service and movement energy are modeled, the schedule uses 37 buses, the depot cases are restricted variants, and neither result is an optimized schedule or operational estimate.
