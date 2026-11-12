# German tariff mechanisms that can make the charging window matter (topic E)

Compiled 12 November 2026. All prices are net network charges, before levies (KWK, §19 surcharge, offshore) and VAT.

**Provenance.** A delegated web search did the first pass. I re-opened and re-extracted the following myself:
- EAM Netz 2026 final price sheet
- EAM Netz 2026 Hochlastzeitfenster (peak-load windows, HLZF) sheet
- the BNetzA AgNes background paper of 27 May 2026

Items marked *(delegated)* were read by the search agent from the primary URL given, but I did not re-open them.

**Question.** A bus moves about 95 kWh/day between the midday window ("early", roughly 10–14) and the overnight window ("late", roughly 20–05). Does any mechanism give an effective early-vs-late spread comparable to the critical spread f/η? With f = 50–300 EUR/bus-day and η ≈ 95 kWh, that is **0.53–3.2 EUR/kWh**.

## 1. Annual capacity charge (Jahresleistungspreis) and the 2,500-hour rule

**Mechanism** (§17(2) StromNEV; §16 and Anlage 4, the simultaneity function — *delegated*: gesetze-im-internet.de/stromnev/__17.html, /__16.html, /anlage_4.html):
- An interval-metered (RLM) customer pays Leistungspreis × annual peak (the highest quarter-hour of the year) plus Arbeitspreis × kWh.
- There are two price pairs, by annual utilisation hours T = kWh / peak kW, below and at or above 2,500 h. They intersect at 2,500 h.
- **The energy price does not depend on time of day.** Only the single annual-peak quarter-hour is time-sensitive.

**2026 prices.**

| DSO, level | LP < 2,500 h (EUR/kW·a) | AP < 2,500 h (ct/kWh) | LP ≥ 2,500 h (EUR/kW·a) | AP ≥ 2,500 h (ct/kWh) | Source |
|---|---|---|---|---|---|
| e-regio Netz, MS | 12.22 | 3.79 | 88.64 | 0.73 | already in the paper (`eregio2026network`); AP values *(delegated)* |
| e-regio Netz, MS/NS | 17.47 | 5.42 | 126.70 | 1.05 | *(delegated)*, same sheet |
| EAM Netz, MS | **20.88** | **4.02** | **114.12** | **0.29** | re-verified; sheet "Preisblatt Netzentgelte Strom final, gültig ab 01.01.2026 bis 31.12.2026" |
| EAM Netz, MS/NS | 46.08 | 6.41 | 166.08 | 1.61 | re-verified, same sheet |
| EAM Netz, monthly LP option, MS | 19.02 EUR/kW per month | 0.29 | | | re-verified, same sheet |

URLs:
- EAM: <https://www.eam-netz.de/fileadmin/user_upload/Ueber_Uns/Netzinformation/Netzentgelte/strom/251215_Preisblatt_EAM_Netz_Strom_2026_-_final.pdf>
- e-regio: <https://cms.e-regio.de/assets/global/Dokumente/Netznutzungsentgelte/2025-12-19-Netzentgelte-Strom-e-regio-Netz-2026.pdf>
- Westnetz 2026 sheet: HTTP 403, not retried.

**Conversion to an effective spread.** The charge applies only if shifting the bus's 95 kWh changes the depot's annual peak. Assume it does, one bus at a time.

| Window that the 95 kWh enters | Added peak | LP (EUR/kW·a) | EUR/a | EUR/kWh, 250 days | EUR/kWh, 365 days |
|---|---|---|---|---|---|
| 4 h | 23.75 kW | 12.22 | 290 | 0.012 | 0.008 |
| 2 h | 47.5 kW | 12.22 | 580 | 0.024 | 0.017 |
| 2 h | 47.5 kW | 88.64 | 4,210 | 0.177 | 0.121 |
| 2 h | 47.5 kW | 114.12 | 5,421 | 0.228 | 0.156 |
| **1 h** (the paper's feeder midday window) | **95 kW** | **114.12** | **10,841** | **0.456** | 0.313 |
| **1 h** | **95 kW** | **166.08** (EAM MS/NS) | **15,778** | **0.664** | 0.455 |

The EUR/kWh columns are LP × kW / (95 kWh × days). Break-even LP for 0.53 EUR/kWh with a 2-h window: 265 EUR/kW·a (250 days) or 387 EUR/kW·a (365 days). With a 1-h window: 132.5 EUR/kW·a at 250 days.

**Reading.**
- Daily shifting into a 2–4 h window never reaches the f/η range. Daily shifting into a **1-hour window above 2,500 h** reaches **0.46–0.66 EUR/kWh**, which is the low end of the range (f ≈ 50–60 EUR/bus-day).
- **The paper's own depot is below 2,500 h.** §8 of the paper states that repeating its windows daily gives at most 1,095 utilisation hours. Under the general tariff, the < 2,500 h Leistungspreis applies (12.22–20.88 EUR/kW·a at MS). Even with a 1-h window that is only 95 kW × 12.22–20.88 / (95 kWh × 250) = **0.05–0.08 EUR/kWh**.
- **The ≥ 2,500 h rows apply to such a depot only in two cases:** other site loads lift its utilisation above 2,500 h, or it uses the §19(2) Wahloption (§2 below). Treat the 0.31–0.66 EUR/kWh row as conditional on that.
- **Direction.** The charge penalizes whichever window sets the annual peak, not "early" per se. With a short midday window and a long overnight window, adding midday energy raises the peak once E/len_early exceeds L/len_late.
- **Ratchet.** If the shift happens on only a few days, one quarter-hour sets the whole year's charge. At 88.64 EUR/kW·a, the first 95 kWh shifted into a 2-h window costs 4,210 EUR, i.e. 44 EUR/kWh. That stays above 3.2 EUR/kWh for the first ~14 shift days and above 0.53 EUR/kWh for ~84 days *(delegated arithmetic, checked)*. A per-day, per-kWh spread cannot represent this cost. It is a max-type, nonseparable cost, which is a convex F(E, L) of the kind the paper already allows: F = LP·max{E/ℓ_E, L/ℓ_L, background} + ….

**Implication for §8 of the paper.** §8 argues that annual capacity savings from choosing between covers are zero, because every feasible minimum-fleet matching admits the balanced point E = S/3. That argument is correct for the *overall* annual peak. It breaks under the window-only rule in §2 below, where the billed quantity is the peak *inside* the operator's peak-load windows, and with it the minimum early load ℓ_m = max(Lo, r_m).

## 2. §19(2) sentence 1 StromNEV: atypical network use (atypische Netznutzung)

**Mechanism.**
- Law text: gesetze-im-internet.de/stromnev/__19.html *(delegated)*. The network operator must offer an individual charge if the customer's peak is foreseeably and significantly off the network's coincident peak. The individual charge is at least 20% of the published charge.
- Implementation per BNetzA BK4-13-739 (11 Dec 2013) **re-verified by me** (decision text pp. 4–5): <https://www.bundesnetzagentur.de/DE/Beschlusskammern/1_GZ/BK4-GZ/2013/2013_bis0999/2013_bis799/BK4-13-0739/BK4-13-0739_Beschluss_DL.pdf?__blob=publicationFile&v=1>
  - The Leistungspreis is billed on the customer's highest load **inside the published HLZF**, not on its annual peak.
  - A customer below 2,500 h may opt for the ≥ 2,500 h price pair.

**Eligibility.**
- Window peak must be below the annual peak by a significance threshold (Erheblichkeitsschwelle). Per BK4-13-739 (re-verified, p. 5 table): HöS 5%, HöS/HS 10%, HS 10%, HS/MS 20%, **MS 20%**, MS/NS 30%, NS 30%.
- Minimum shift: **100 kW at all levels** (re-verified on the EAM HLZF sheet, p. 2).
- Minimum saving (Bagatellgrenze): **500 EUR/a** (re-verified on the EAM sheet, p. 2).
- Caveat: the EAM sheet's threshold column did not extract in reliable order. Its prose confirms 30% for NS.
- Windows apply Monday–Friday only; 24 Dec–1 Jan, weekends and holidays are off-peak (re-verified, EAM sheet p. 1).

**2026 windows.**

EAM Netz, re-verified; file dated 6 Oct 2025; seasons per BK4-13-739:
<https://www.eam-netz.de/fileadmin/user_upload/Ueber_Uns/Netzinformation/Netzentgelte/strom/251002_UEbersicht_der_HLZ_2026_EAMN.pdf>

| Level | Winter (Jan–Feb, Dec) | Spring | Summer | Autumn (Sep–Nov) |
|---|---|---|---|---|
| MS | **10:00–14:15** | none | 12:30–14:15, 15:00–15:30 | 08:30–12:45, 17:15–20:00 |
| MS/NS | 16:45–20:15 | none | none | 18:00–18:30 |

N-ERGIE Netz, *(delegated)*; dated 31 Oct 2025:
<https://www.n-ergie-netz.de/public/remotemedien/media/nng/infothek_3/veroeffentlichungen_1/weitere_veroeffentlichungen/N_Hochlastzeitfenster_2026_NNG.pdf>

| Level | Winter | Spring | Summer | Autumn |
|---|---|---|---|---|
| MS | 07:45–09:00, 16:30–19:15, 19:30–19:45 | none | none | 16:45–18:45 |

e-regio Netz windows were **not found**, and none were fabricated. Without them, the Euskirchen case in the paper cannot be evaluated under §19(2).

**Effective spread.**
- **EAM MS (midday inside the HLZF, night outside).** Each kW of midday window load costs 114.12 EUR/kW·a, and night load is free. Using the conversions in §1:
  - 0.228 EUR/kWh (2-h midday window, 250 days)
  - **0.456 EUR/kWh (1-h window, 250 days)**
  - 0.08–0.11 EUR/kWh if the charge is spread over 4 h
- **N-ERGIE MS.** Neither the 10–14 nor the 20–05 window lies in an HLZF, so the spread is 0.
- **Cliff.** If midday charging pushes the window peak above (1 − 20%) of the annual peak at MS, eligibility is lost and the whole general charge returns. That is a discrete jump of up to tens of thousands of EUR/a for a ~1 MW depot (illustrative). It is another nonconvexity, on the *supply* side.
- **Relevance to the bus-fee comparison.** Under atypical billing with the Wahloption (re-verified in BK4-13-739), the billed quantity is the midday peak, and minimizing it means E = ℓ_m = max(Lo, r_m). So the matching's forced early charge r_m enters the bill directly. One extra pair with forced charge η adds about η/len_early kW of window peak. Example: η = 95 kWh in a 1-h window adds 95 kW × 114.12 = 10,841 EUR/a. That is comparable to one bus-day fee of 50 EUR over 217 days (10,850 EUR). At EAM-type windows the tariff reaches the f/η threshold only for cheap buses (f ≈ 50) and short windows.

**Legal status, November 2026.**
- StromNEV rules lapse on **31 Dec 2028**. Re-verified in the BNetzA AgNes background paper of 27 May 2026: the provisions "zum 31.12.2028 vom Deutschen Bundestag aufgehoben werden mussten" ("had to be repealed by the Bundestag as of 31.12.2028"). <https://www.bundesnetzagentur.de/SharedDocs/Pressemitteilungen/20260527_AgnesPapier.pdf?__blob=publicationFile&v=1>
- Same paper (re-verified): "Die atypische Netznutzung erfährt keine generelle Verlängerung" ("atypical network use is not generally extended"). The discount structure is kept transitionally only for industrial atypical users with **≥ 10 GWh/a**. Bandlast is extended to 31 Dec 2031 for existing customers.
- AgNes draft determination GBK-25-01-1#3 (published 6 Aug 2026; consultation closed 18 Sep 2026) *(delegated)*. The transition requires an agreement valid on 31 Dec 2028, eligibility at least once in 2026–2028 and average > 10 GWh/a. 2029–2031 discounts are frozen. **I found no evidence of final adoption by 12 Nov 2026.**
- Consequence: a bus depot (well below 10 GWh/a) can use §19(2) S.1 only through 2028.

## 3. §14a EnWG time-variable network charge (Modul 3)

**Source.** BNetzA BK8-22/010-A, 23 Nov 2023, billing from 1 Apr 2025 *(delegated)*:
<https://www.bundesnetzagentur.de/DE/Beschlusskammern/1_GZ/BK8-GZ/2022/2022_4-Steller/BK8-22-0010/BK8-22-0010-A_Festlegung_DL_BF.pdf?__blob=publicationFile&v=6>

**Structure.**
- Three-tier energy price (HT/ST/NT) for controllable consumption devices > 4.2 kW, chosen on top of Modul 1.
- HT at least 2 h/day, at most 100% above ST. NT 10–40% of ST. Applies in at least two quarters.
- Tenor 3(e): available **only at metering points without RLM interval metering** ("ohne registrierende Leistungsmessung").
- The low-voltage scope rests on DSO and secondary documents. The BK6-22-300 text itself was not verified.

**Applicability.** **Not applicable to an MV, RLM-metered depot.** An e-regio sheet line suggests interval-metered operators can choose Modul 3. That contradicts the tenor as read and is unresolved.

**Magnitudes** *(delegated; illustrative only)*:

| DSO 2026 | NT | ST | HT | Early (10–14) vs late (20–05) |
|---|---|---|---|---|
| EAM Netz | 1.64 ct (23–06, 11–15) | 5.48 ct | 10.52 ct (17–22) | early cheaper by about 1.4 ct/kWh |
| e-regio | 3.61 ct (0–6) | 9.02 ct | 15.46 ct (15–20) | late cheaper by about 3.0 ct/kWh |

Both spreads are below 0.05 EUR/kWh.

## 4. Wholesale and other mechanisms

**Day-ahead spot.** Computed by the delegated agent from SMARD hourly DE-LU prices, 2024-01-01 to 2026-11-12. I did not re-run it. SMARD's terms-of-use caveat in the 2 Nov OPF review applies. Early = mean of 10–14; late = mean of 20–24 and 00–05.

| Year | Mean late − early | Median | Share of days early cheaper | Winter mean |
|---|---|---|---|---|
| 2024 | +23.8 EUR/MWh | +17.9 | 70% | negative, −20 to −9 |
| 2025 | +38.6 EUR/MWh | +31.5 | 77% | |
| 2026 YTD | +68.6 EUR/MWh | +72.1 | 81% | |

- Midday is usually *cheaper* (solar).
- The largest single day is about 0.35 EUR/kWh. Typical values are **0.02–0.07 EUR/kWh**.
- It reaches the depot only via a spot-indexed or §41a EnWG dynamic tariff (mandatory offer since 1 Jan 2025 for customers with an intelligent meter; *delegated*).

**AgNes from 2029.** Re-verified in the 27 May 2026 paper: for consumers > 100,000 kWh/a, today's Leistungspreis is replaced by a **Kapazitätspreis (EUR/kW·a) on booked capacity plus a ct/kWh surcharge for exceeding it**, with an energy price within the booking.
- No time-of-day element.
- Per the draft *(delegated)*, the overrun price AP2 is 200–350% of AP1.
- The paper's timetable (re-verified): dynamic network charges for storage in 2030 at the earliest, preferably by 2033; for feed-in in 2032 at the earliest.
- A separate determination on industrial special charges is planned for 2027.

**§118(6) EnWG** storage exemption: relevant only to V2G exports fed back into the same network; not pursued.

## 5. Summary

| Mechanism | Applies to MV RLM depot, Nov 2026 | Direction | Effective spread (EUR/kWh) | Reaches 0.53–3.2? |
|---|---|---|---|---|
| Annual-peak LP, < 2,500 h | yes | whichever window sets the peak | 0.01–0.04 | no |
| Annual-peak LP, ≥ 2,500 h, 2-h window | yes | same | 0.12–0.33 | no |
| Annual-peak LP, ≥ 2,500 h, 1-h window | only if the site is ≥ 2,500 h (not the paper's depot, ≤ 1,095 h from buses) | same | 0.31–0.66 | low end only (f ≈ 50–60), conditional |
| Annual-peak LP, < 2,500 h, 1-h window (the paper's depot) | yes | same | **0.05–0.08** | no |
| Ratchet (few shift days) | yes | same | up to 44 on the first day | yes, but a max-type cost, not a spread |
| §19(2) S.1 atypical, EAM-type windows, with Wahloption (≥ 2,500 h pair billed on window peak) | yes until 2028 (if thresholds met) | midday penalized, night free | 0.08–0.46 | approaches the low end only with a 1-h window |
| §19(2) S.1, N-ERGIE-type windows | yes until 2028 | neither | 0 | no |
| §14a Modul 3 | no | — | < 0.05 | no |
| Day-ahead spot / §41a | via contract | midday cheaper | 0.02–0.07 | no |
| AgNes 2029+ | draft | none (booking plus overrun) | — | no |

**For the planned experiment.**
- Model the capacity charge as a convex max-type cost on window peaks, not as a per-kWh spread.
- The relevant case for a ≤ 1,095 h depot is §19(2) atypical use with the Wahloption. BK4-13-739 (re-verified) lets a < 2,500 h customer bill the ≥ 2,500 h Leistungspreis on its **highest load inside the HLZF**, with the ≥ 2,500 h Arbeitspreis on all energy.
- Use EAM Netz MS 2026 (LP 114.12 EUR/kW·a; HLZF winter 10:00–14:15) as the one documented case where the midday window is penalized and the overnight window is not.
- Billed quantity = midday peak. Its minimum is ℓ_m/len_early, so r_m enters directly. Eligibility also requires a ≥ 20% gap between window peak and annual peak and a ≥ 100 kW shift, and the regime ends in 2028 for depots below 10 GWh/a.
- Test 1-h and 2-h midday windows. The bus-fee threshold is approached only for f ≈ 50–60 EUR/bus-day with a 1-h window.
- Under the general tariff, the paper's depot sees at most 0.05–0.08 EUR/kWh and no support failure is expected.
- Present the result as a boundary, not as typical German exposure.
