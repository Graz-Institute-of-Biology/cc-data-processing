# ATTO Tree Surface-Area — Project Notes

**Status (2026-07-07):** Terra Firme height model **done for now** (Chave-E, validated).
Campinarana now on a **local-calibrated Michaelis–Menten allometry** (anchored to
Targhetta 2015 white-sand structure at the ATTO site; replaces the Feldpausch placeholder)
with a **±13% stature band** folded into its surface area. Crown still a `1.5×`
placeholder. Next: obtain raw local H–D pairs (ATTO/MAUA group) to upgrade the campinarana
curve from summary-anchor to fitted, and a **cheap crown-share fallback** (Chambers
whole-tree) — see §7.

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
- Crown surface area is being derived **separately by the partner group** (JKI /
  Waldlabor) from RGB imagery; here it is a `1.5×` placeholder. Because that route may be
  slow, a cheap, independent **crown-share fallback** (via the Chambers whole-tree
  allometry) is planned — see §7.

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
- **Michaelis–Menten (Campinarana, local calibration)** — the campinarana model now used:
  `H = Hmax·D / (b1 + D)`, with **Hmax = 24 m** (from the local ~22 m canopy ceiling) and
  **b1 = 15.0** (pinned so `H(18 cm) = 13.1 m`, Targhetta 2015's community mean). MM was
  the best-fit form for campinarana in the Roraima oligotrophic-forest H–D study, where
  the white-sand asymptote is distinct from terra firme and pantropical curves overshoot
  by up to ~106%. Unlike a log-linear curve it **flattens to a ceiling**, so even the
  110 cm stem tops out at 21 m. See §5 for why this beats the alternatives.

**Which model each forest uses:** Terra Firme → Chave-E; Campinarana → Michaelis–Menten
(config `HEIGHT_MODEL` in `plot_area_estimation.py`).

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
- **Campinarana → local-calibrated Michaelis–Menten** (replaces the Feldpausch
  placeholder). Anchored to **Targhetta et al. 2015**, a campinarana inventory at the
  Uatumã SDR *next to the ATTO tower* (same ATTO project): measured mean H **13.1 m**
  (DBH ≥ 10 cm), canopy ceiling **~22 m**. Over our DBH ≥ 20 inventory the MM curve gives
  **mean H 16.1 m, max 21.1 m** (≤ ceiling ✓); it recovers ~13 m over a simulated ≥ 10 cm
  population. Why MM and not the others:
  - **Chave-E** → mean 25.2 m, max 46 m: absurd for a stunted white-sand forest (E can't
    separate the forests, so it just copies the Terra Firme curve).
  - **Feldpausch placeholder** → mean 17.3 m but **max 32 m**: has no asymptote, so the
    biggest stems become taller than any campinarana ever measured.
  - **Woortmann 2018-style correction** (`H = 0.637·H_ChaveE`, one stature factor on the
    terra-firme curve) → fixes the *mean* (16.1 m) but keeps the pantropical curvature, so
    big stems still overshoot to **29 m**. Fine as a cross-check; MM (real ceiling) is the
    keeper. (Woortmann applied their factor to the *biomass* eq, where an over-tall tail
    matters less than it does for a per-tree height feeding a surface-area calc.)
- **Campinarana stature band folded in: stem SA = 3,558 ± 454 m²/ha (±13%)**, from
  recalibrating MM at Targhetta's 13.1 ± 2.6 m (ceiling held fixed). The old Feldpausch
  placeholder (3,994 m²/ha) sits at the *high* edge of this band. Tighter than Terra
  Firme's band because campinarana now has a local stature anchor.
- **On Terra Firme the ~24% remains the dominant uncertainty.** Chave-E reads ~+7% high,
  Feldpausch ~−8% low vs measured heights, so the truth is between them; the height-model
  choice is a wider band than any other assumption (taper, etc.).
- **Chambers magnitude match ≠ proof.** It confirms the right order of magnitude but
  **cannot referee Chave-E vs Feldpausch**, because (a) the crown 1.5× is a free knob that
  absorbs the difference, and (b) Chambers is > 10 cm DBH while the inventory is ≥ 20 cm
  (so the ATTO total should sit somewhat below the raw Chambers number).

---

## 6. Open issues / caveats

- **Crown = 1.5 × stem is a placeholder**, not a result (fixes crown share at 60% by
  construction). Partner group / Chambers allometry to replace it.
- **Campinarana curve rests on summary anchors, not raw pairs** — MM is calibrated to
  Targhetta 2015's *published mean + ceiling*, not to individual H–D measurements. Sound
  and validated against the ≥10 cm mean, but the clean upgrade is real local pairs (the
  ATTO/MAUA group measured ~1,849 campinarana heights with DBH). Villa Zegarra 2017 (70
  harvested campinarana trees, RDS Uatumã) and Woortmann 2018 would also serve — both
  currently un-downloadable.
- **Validation is not fully independent** — the Chave harvest trees overlap the data the
  Feldpausch/Chave models were trained on. It's a strong consistency check, not a clean
  out-of-sample test.
- **Height-model uncertainty is now propagated for Campinarana (±13% band, §5) but not yet
  for Terra Firme (~24%).**

---

## 7. Next steps (deferred — for a fresh session)

Ordered by leverage.

1. **Get the raw campinarana H–D pairs from the ATTO/MAUA group** (Wittmann/Targhetta) —
   they measured ~1,849 campinarana trees with paired DBH + clinometer height *at the ATTO
   site*. This upgrades the MM curve from summary-anchor to a genuinely fitted local
   allometry, and gives *independent* validation for the Terra Firme height too (the Chave
   check leans on non-independent harvest data). Also worth: local TLS/LiDAR, or GEDI
   canopy heights over the campinarana polygons as an independent ceiling check.
2. **Campinarana height allometry — DONE (interim, 2026-07-07):** local-calibrated
   Michaelis–Menten anchored to Targhetta 2015, with a ±13% stature band (§3, §5). Replace
   with a fitted curve once the raw pairs from step 1 land.
3. **Crown share via the Chambers 2004 whole-tree allometry** — a *wanted deliverable*,
   not just validation: the partner team derives crown from RGB imagery but may be slow,
   so we want a **cheap, defensible fallback**. Chambers gives total woody area
   (bole **+ branches**) from DBH, so:
   `crown ≈ Chambers_total(DBH) − frustum_trunk(DBH, H)`.
   One allometry both validates the trunk and retires the fixed `1.5×`. Needs the exact
   coefficients from the paper. Cleanest for Terra Firme (central-Amazon terra firme);
   Campinarana crown stays an approximation.
   - **Compatibility (good news):** the partner output is woody *crown-branch* area
     (drone imagery + leaf-flush phenology tracking), **not** a leaf envelope — the same
     quantity class as Chambers and our bark-surface trunk. Confirm when their data lands
     whether it is a 2D *projected* branch area or a 3D reconstruction (SfM), since our
     trunk / Chambers are 3D *surface* area (a projected→surface factor may be needed).
   - **Local validation loop:** they can segment crown-branch area for *some plots where
     we have DBH* — the local crown ground-truth we currently lack. So use the Chambers
     share as the interim estimate, then validate / recalibrate it against their per-plot
     data when it arrives (a locally-fitted crown share could replace the borrowed
     Chambers one).
4. *(Optional)* **Terra Firme height band** — do for TF what was done for Campinarana
   (§5): report the ~24 % Chave-vs-Feldpausch height-model spread as a ± band rather than
   a single committed value.
5. *(Optional)* **Biomass forward check** — frustum volume × species-level wood density
   (inventory has `GEN`/`SPP`) vs Chave-2014 AGB. On Manaus, Chave AGB already reproduces
   measured biomass to ~+5 % median, so the reference is solid.

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
- **Targhetta, Kesselmeier & Wittmann 2015**, *Folia Geobotanica* 50:185–205 — campinarana
  (+ igapó) structure at the Uatumã SDR *next to the ATTO tower*: mean H 13.1 m, ceiling
  ~22 m. The local anchor for the campinarana Michaelis–Menten curve. (PDF on disk:
  OneDrive `…/03_Literature/s12224-015-9225-9.pdf`.)
- **Roraima oligotrophic-forest H–D study** (*Modelos alométricos… florestas oligotróficas
  do norte da Amazônia*, 2024, UFRR/PRONAT) — Michaelis–Menten best-fit for campinarana;
  white-sand asymptote distinct from terra firme; pantropical curves overshoot by ≤106%.
- **Woortmann et al. 2018**, *Acta Amazonica* 48:85–92 — campinarana biomass; dominant-
  height correction of terra-firme equations (basis for the §5 Woortmann cross-check).
- **Villa Zegarra 2017**, MSc dissertation INPA — 70 harvested campinarana trees at RDS
  Uatumã with fitted D/H/biomass equations (target source for a fitted local curve;
  currently un-downloadable).
- **Global Wood Density Database** (Zanne/Chave 2009) — species-level wood density.
