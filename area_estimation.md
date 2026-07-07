# Tree Surface-Area Estimation

How per-tree **main stem** surface area is estimated in
[plot_area_estimation.py](plot_area_estimation.py), which input fields drive it,
and the assumptions behind each step. For project status, validation results and
next steps, see [ATTO_surface_area_NOTES.md](ATTO_surface_area_NOTES.md).

> **Scope:** this document covers the **main stem** estimate, derived from the
> field data plus the Chave `E` climate grid sampled at each plot (see §2). The
> **crown** contribution is currently a placeholder (`crown = 1.5 × main_stem`)
> and will be replaced by a separate model — see the **Crown area** section (§5).
>
> *(The older `tree_surface.py` is deprecated; `plot_area_estimation.py` is the
> current analysis file.)*

---

## 1. Data source & fields

Source: `Tree_data/ATTO/plots/JKI_AG-Waldlabor_ATTO_Faulhammer_.xlsx`
(one row per inventoried tree, DBH >= 20 cm).

| Field    | Used for | Notes |
|----------|----------|-------|
| `DBH`    | stem radius **and** height | diameter at breast height, **cm** |
| `POS`    | forest-type split | `Pla` = Terra Firme, `Caa` = Campinarana; selects the **height model** and coefficients (see §2) |
| `LON` / `LAT` | Chave `E` lookup | plot coordinates; used to sample the `E` parameter from `E.nc` (see §2) |
| `CODE`   | area normalization | plot identifier; distinct plots are counted per forest to get ground area |
| `STATUS` | *(not applied — all trees kept)* | `live` / `std` / `snap` / `upr`; see **Tree status** below |

The blank trailing rows in the sheet (no `POS`/`CODE`) are ignored by the
`POS in {Pla, Caa}` filter.

---

## 2. Height estimation (per-forest model)

Height is estimated from DBH. **Each forest uses its own model**, selected in code
by `HEIGHT_MODEL`. The choice was made after validating both models against real
harvested Amazon trees (`validate_height.py`; results in the NOTES).

### Terra Firme — Chave et al. 2014 (validated)

```
ln H = 0.893 − E + 0.760 * ln(DBH) − 0.0340 * (ln DBH)^2
```

`E` is the Chave environmental-stress parameter, sampled **per plot** (bilinear)
from the `E.nc` grid at each plot's `LON`/`LAT` (≈ −0.105 at ATTO). Against real
measured heights this model is essentially **unbiased** (bias +0.4 m, RMSE 3.4 m),
so it drives Terra Firme.

### Campinarana — Feldpausch et al. 2011 (placeholder)

```
H = exp( beta0 + beta1 * ln(DBH) + kappa )
```

| `POS` | region / class | beta0 | beta1 | kappa |
|-------|----------------|-------|-------|-------|
| `Caa` | Guyana Shield, **Dry** | 1.1064 | 0.5002 | 0.0109 |
| `Pla` | Guyana Shield, **Moist** (Terra-Firme alternative) | 1.2597 | 0.5002 | 0.0109 |

> **Important:** `Dry` / `Moist` / `Wet` are Feldpausch **precipitation classes,
> not forest types.** Both ATTO forests sit in the same (Moist) climate, so this
> does **not** encode the Terra-Firme-vs-Campinarana difference. Campinarana is
> kept on the **Dry** coefficients only as an *unvalidated* stand-in for its
> shorter white-sand stature — there is no white-sand site in the harvest data to
> validate it, and Chave-E cannot separate it from Terra Firme (near-identical
> `E`). A dedicated Campinarana allometry is a pending task.

**Uncertainty.** The height-model choice is the **dominant** uncertainty in the
estimate: for Terra Firme, Chave-E gives ~24 % more stem area than Feldpausch
(Chave-E reads ~+7 % high, Feldpausch ~−8 % low vs measured heights, so the truth
lies between them). Full coefficient table:
[feldpausch_coefficients.csv](feldpausch_coefficients.csv).

---

## 3. Stem radii & taper

Radii are derived from DBH (in cm):

```
Radius_bottom = DBH / 2
Radius_top    = 0.7 * Radius_bottom
```

The **0.7 taper factor** (top radius = 70 % of breast-height radius) was set in
consultation with a domain specialist. It is a fixed constant and the best
available estimate at this stage; the main-stem area scales linearly with the
`(Radius_bottom + Radius_top)` term, so it is directly sensitive to this value.

---

## 4. Main-stem surface area

The main stem is modelled as the **lateral surface of a truncated cone
(frustum)**, using tree height as the length and the mean of the two radii:

```
SA_main_stem = H * pi * ( Radius_bottom/100 + Radius_top/100 )
```

- `/100` converts the radii from cm to m, so `SA_main_stem` is in **m²**.
- Uses vertical height `H` in place of the frustum slant height. For tall, low-
  taper stems the two are nearly equal, so this slightly **under-estimates** the
  true lateral area; the error grows with taper.

---

## 5. Crown area (placeholder)

```
SA_crown = 1.5 * SA_main_stem
SA_total = SA_main_stem + SA_crown
```

The `1.5` multiplier is a **temporary placeholder** so that totals are
non-trivial. It will be replaced by a dedicated crown model. Consequently the
crown share is a fixed 60 % of total by construction and should **not** be
interpreted as a result.

As a magnitude check, Terra-Firme stem area (~7.4k m²/ha) plus this placeholder
crown gives ~18k m²/ha total woody area — inside the **Chambers et al. 2004**
benchmark of 17–21k m²/ha (central Amazon, > 10 cm DBH). The Chambers per-tree
allometry is the intended replacement for this placeholder, since it constrains
height and crown together.

---

## 6. Area normalization (per hectare)

The inventory contains **multiple plots per forest** (one per `CODE`):
9 Terra Firme plots, 6 Campinarana plots. Each forest's ground area is:

```
area_ha = (number of plots for that forest) * PLOT_AREA_HA
```

`PLOT_AREA_HA` derives from the single-plot size constant `PLOT_SIZE_M2` at the
top of the analysis block. Per-hectare metrics (`Stem_density_per_ha`,
`SA_m2_per_ha`, `Basal_area_m2_per_ha`) all scale off this one value.

Plot dimensions are **confirmed at `20 x 60 m` = 1200 m² (0.12 ha)** per plot
(`PLOT_SIZE_M2 = 20 * 60`). Per-hectare metrics scale off this constant; the
Terra-Firme : Campinarana ratio depends only on the plot counts, not on this
value.

---

## 7. Basal area (reference / cross-check)

```
Basal_area = pi * (DBH/200)^2      # m² per tree; /200 -> radius in m
```

Basal area is computed **straight from measured DBH** with no model, taper, or
crown assumption, so it is the assumption-free anchor for comparing the two
forests and sanity-checking the surface-area totals.

---

## Tree status (all trees included — confirmed)

The `STATUS` field distinguishes tree condition:

| STATUS | meaning | count |
|--------|---------|-------|
| `live` | living | 417 |
| `std`  | standing dead | 30 |
| `snap` | snapped | 10 |
| `upr`  | uprooted | 2 |

**All trees (live and dead) are intentionally included.** Confirmed in a project
meeting that filtering by `STATUS` does not make a meaningful difference to the
estimates, so no `STATUS` filter is applied.
