# ATTO Tree Surface-Area — Project Notes

**Status (2026-07-07):** Terra Firme height model **done for now** (Chave-E, validated).
Campinarana on an unvalidated placeholder. Crown still a placeholder. Next block of
work gated on finding *independent* validation data.

This is the **overview / status / next-steps** note. For the step-by-step method of the
surface-area calculation see [`area_estimation.md`](area_estimation.md).

---

## 1. What we're trying to do

Produce defensible **per-tree and per-hectare woody surface-area** estimates for the two
ATTO forest types, from a DBH-only field inventory, and **ground them in real Amazon
measurements** so the numbers can be trusted (and later fine-tuned).

- Site: ATTO (Amazon Tall Tower Observatory), central Amazon, ~2.1° S, 59.0° W.
- Two forest types, a few km apart: **Terra Firme** (`POS = Pla`) and **Campinarana**
  (white-sand, `POS = Caa`).
- Inventory: one row per tree, **DBH ≥ 20 cm**, **all stems** (live + dead) included.
- Plot size: **20 × 60 m = 1200 m² = 0.12 ha**. Terra Firme = 9 plots (1.08 ha),
  Campinarana = 6 plots (0.72 ha).
- Crown surface area is handled **separately by the partner group** (JKI / Waldlabor);
  here it is a placeholder so totals are non-trivial.

**The pipeline:** `DBH → height (allometry) → stem surface area (truncated cone) →
+ crown (placeholder) → aggregate per plot / per forest / per hectare.`

---

## 2. The estimation method (short version)

| Step | Formula | Notes |
|---|---|---|
| Stem radii | `r_bottom = DBH/2`, `r_top = 0.7·r_bottom` | taper 0.7 = specialist-set constant |
| Height | see §3 | the main lever; validated this session |
| Stem SA | `SA_stem = H · π · (r_bottom + r_top)` (m², radii→m) | lateral area of a truncated cone |
| Crown SA | `SA_crown = 1.5 · SA_stem` | **placeholder** — not a result |
| Basal area | `BA = π·(DBH/2)²` | model-free cross-check anchor |

Frustum volume (for the biomass cross-check): `V = (π·H/3)·(r_b² + r_b·r_t + r_t²)`.

---

## 3. Height models (the validated part)

Two candidates, both applied from DBH:

- **Feldpausch et al. 2011** (regional): `H = exp(β0 + β1·lnD + κ)`, `κ = 0.0109`.
  Guyana-Shield Moist β0 = 1.2597, β1 = 0.5002. **Important:** the Dry/Moist/Wet
  columns of the Feldpausch table are **precipitation classes, not forest types** — see
  §5. Clean table saved as [`feldpausch_coefficients.csv`](feldpausch_coefficients.csv).
- **Chave et al. 2014** (pantropical, E-based):
  `ln H = 0.893 − E + 0.760·lnD − 0.0340·(lnD)²`,
  with `E` = environmental-stress parameter sampled **per plot** from `E.nc`
  (bilinear). Sampled values: Terra Firme **E ≈ −0.1054**, Campinarana **E ≈ −0.1106**.

Related equations used in cross-checks:
- Chave 2014 biomass: `AGB = 0.0673·(ρ·DBH²·H)^0.976` (kg; ρ = wood density g/cm³).

---

## 4. What we did (this work block)

1. **Located the validation data** already on disk: the Chave 2014 pantropical package
   (`Tree_data/ATTO/pantropical_allometry/...`) — `E.nc` (E grid), `CWD.nc`, and, most
   usefully, `Chave_GCB_Direct_Harvest_Data.csv` = **4004 real harvested trees**
   (DBH, height, AGB, wood density) across 58 sites, incl. `BraMan2` (Manaus, the
   near-local analog).
2. **Validated the height models** against 523 real measured heights from central /
   Guyana-Shield Amazon sites (`validate_height.py`). Result table below.
3. **Wired Chave-E into the pipeline** (`plot_area_estimation.py`) for Terra Firme, kept
   config-driven via `HEIGHT_MODEL`. Both height models are computed so the impact is
   visible (`impact_report()`).
4. **Cross-checked magnitude** against the Chambers 2004 total-woody benchmark.

**Height validation — model vs 523 real measured heights** (pred − measured):

| Height model | bias | RMSE | verdict |
|---|--:|--:|---|
| **Chave-2014 E** (E.nc) | +0.4 m (+7%) | **3.4 m** | best; ~unbiased across DBH |
| Feld Guyana-**Moist** (was TF) | −2.2 m (−8%) | 4.2 m | slightly low, worse for big trees |
| Feld Guyana-**Dry** (was Caa) | −4.1 m (−21%) | 5.6 m | |
| Feld Brazilian-Moist | −4.3 m (−22%) | 5.9 m | |
| Feld East-Central-Moist | −5.7 m (−32%) | 7.1 m | **rejected** → confirms Guyana Shield |

**Surface-area impact of the switch** (Terra Firme):

| | mean H | stem SA /ha | + crown (×1.5) → total woody /ha |
|---|--:|--:|--:|
| Feldpausch | 21.1 m | 5,921 | 14,800 |
| **Chave-E (now used)** | 26.2 m | **7,355** | **18,400** |

→ **Terra Firme stem SA +24.2%.** The total-woody figure (18.4k/ha) lands inside the
**Chambers 2004 benchmark of 17,000–21,000 m²/ha** (central Amazon, > 10 cm DBH).

---

## 5. Key findings & decisions

- **`E` cannot separate the two forest types.** They sit in the same ~5 km climate cell,
  so E differs by ~1% → Chave-E gives Terra Firme ≈ Campinarana height. The forest-type
  distinction has **no principled home** in either E or Feldpausch.
- **The Feldpausch TF/Caa split was a mis-mapping.** The code's `β0 = 1.2597` (TF) vs
  `1.1064` (Caa) are Guyana-Shield **Moist vs Dry precipitation** coefficients — *not*
  forest types. Both ATTO forests are Moist (~2100–2400 mm/yr). Using "Dry" for
  Campinarana is only a proxy for its shorter stature (right direction, wrong axis).
- **Region resolved: Guyana Shield**, not East-Central Amazonia (which under-predicts
  real heights by 32%).
- **Terra Firme → Chave-E** (validated, ~unbiased). Stem SA rises +24% vs Feldpausch.
- **Campinarana → kept on Feldpausch placeholder.** Applying Chave-E would push its mean
  height to 25.2 m ≈ Terra Firme (26.2 m) — clearly wrong for a stunted white-sand forest.
- **The 24% is the dominant uncertainty.** Chave-E reads ~+7% high, Feldpausch ~−8% low
  vs measured heights, so the truth is between them; the height-model choice is a wider
  band than any other assumption (taper, etc.).
- **Chambers magnitude match ≠ proof.** It confirms the right order of magnitude but
  **cannot referee Chave-E vs Feldpausch**, because (a) the crown 1.5× is a free knob that
  absorbs the difference, and (b) Chambers is > 10 cm DBH while the inventory is ≥ 20 cm
  (so the ATTO total should sit somewhat below the raw Chambers number).

---

## 6. Open issues / caveats

- **Crown = 1.5 × stem is a placeholder**, not a result (fixes crown share at 60% by
  construction). Partner group / Chambers allometry to replace it.
- **Campinarana height is unvalidated** — no white-sand site exists in the harvest data.
- **Validation is not fully independent** — the Chave harvest trees overlap the data the
  Feldpausch/Chave models were trained on. It's a strong consistency check, not a clean
  out-of-sample test.
- **Height-model uncertainty (~24%)** is currently un-propagated into the reported SA.

---

## 7. Next steps (deferred — for a fresh session)

1. **Find independent validation data** — local ATTO measured heights / LiDAR / TLS.
   This is the gate: it's what turns the consistency check into a real test and lets us
   fine-tune / choose between height models.
2. **Chambers 2004 per-tree total-woody SA allometry** — get the exact coefficients
   (whole-tree bark area from DBH, 315 felled central-Amazon trees). This is the real
   referee: it constrains height **and** crown together and **replaces the 1.5× crown
   placeholder**. Benchmark already known: 17–21k m²/ha (> 10 cm DBH).
3. **A dedicated Campinarana (white-sand) height allometry** — the one genuine gap.
4. *(Optional)* Add an **averaged / envelope** height option so the ~24% model
   uncertainty is reported as a ± band rather than a single committed value.
5. *(Optional)* **Biomass forward check** — frustum volume × species-level wood density
   (inventory has `GEN`/`SPP`) vs Chave-2014 AGB. On Manaus, Chave AGB already reproduces
   measured biomass to ~+5% median, so the reference is solid.

---

## 8. File map

| File | Role |
|---|---|
| [`plot_area_estimation.py`](plot_area_estimation.py) | **Main analysis** + presentation figures; height model is config-driven (`HEIGHT_MODEL`) |
| [`validate_height.py`](validate_height.py) | Height-model validation vs Chave harvest data |
| [`feldpausch_coefficients.csv`](feldpausch_coefficients.csv) | Clean Feldpausch 2011 table (region × precip class) |
| `feldpausch_coefficients_table.txt` | Raw pasted table (source) |
| [`area_estimation.md`](area_estimation.md) | Step-by-step method detail |
| `tree_surface.py` | **Deprecated** earlier version (superseded by `plot_area_estimation.py`) |
| `Tree_data/ATTO/plots/JKI_AG-Waldlabor_ATTO_Faulhammer_.xlsx` | Field inventory |
| `Tree_data/ATTO/pantropical_allometry/…/E.nc` | Chave E grid (var `layer`) |
| `Tree_data/ATTO/pantropical_allometry/…/Chave_GCB_Direct_Harvest_Data.csv` | Real harvested trees (ground truth) |
| `figures_area_estimation/` | Output figures (incl. `fig_height_validation.png`) |

---

## 9. References

- **Chave et al. 2014**, *Global Change Biology* — pantropical AGB & E-based height.
- **Feldpausch et al. 2011**, *Biogeosciences* — regional height–diameter allometry.
- **Chambers et al. 2004**, *Ecological Applications* 14:72–88 — whole-tree woody surface
  area from DBH (Amazon); benchmark 17–21k m²/ha. *(coefficients still to be retrieved)*
- **Global Wood Density Database** (Zanne/Chave 2009) — species-level wood density.
