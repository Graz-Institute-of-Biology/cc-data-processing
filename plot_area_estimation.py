"""
Presentation figures: tree height & MAIN-STEM surface-area estimation (ATTO plots).

Pipeline visualised (one figure per step):
    plot inventory (DBH)                      -> Fig 1
    -> tree height   (Chave-E: Terra Firme · Feldpausch: Campinarana) -> Fig 2 (Step 1)
    -> trunk geometry (truncated cone, taper) -> Fig 3  (Step 2)
    -> main-stem lateral surface area         -> Fig 4  (Step 3)
    -> estimation bandwidth (mean ± SD)        -> Fig 5

Crown surface area is estimated separately by the partner group and is
deliberately NOT included here.

Settings (both confirmed):
    PLOT_SIZE_M2  -- single-plot ground area (20 x 60 m = 1200 m²), drives
                     per-hectare numbers
    LIVE_ONLY     -- kept False: all stems (live + dead) are included, as
                     status was confirmed not to change the estimates
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

# --------------------------------------------------------------------- config
XLSX = r"Tree_data/ATTO/plots/JKI_AG-Waldlabor_ATTO_Faulhammer_.xlsx"
OUTDIR = Path("figures_area_estimation")
OUTDIR.mkdir(exist_ok=True)

PLOT_SIZE_M2 = 20 * 60      # confirmed: 20 x 60 m = 1200 m² per plot
LIVE_ONLY = False           # confirmed: include all stems (status doesn't change estimates)
TAPER = 0.7                 # top radius / bottom radius (specialist-set, fixed)

# Height from DBH — candidate models, validated in validate_height.py against
# real measured Amazon heights (Chave direct-harvest data):
#   "chave": Chave et al. 2014 pantropical, H = exp(0.893 - E + 0.760 lnD - 0.0340 lnD^2),
#            with E (environmental stress) sampled per plot from E.nc. Best fit to
#            measured central/Guyana-Shield heights (bias +0.4 m, RMSE 3.4 m).
#   "feld" : Feldpausch et al. 2011 regional, H = exp(b0 + b1 lnD + k).
#   "mm"   : Michaelis-Menten H = Hmax*D/(b1+D), calibrated to LOCAL campinarana
#            structure (see CAMPINARANA_MM). Campinarana only.
# The Feldpausch b0 pair below is Guyana-Shield MOIST (TF) vs DRY (Caa) — but Dry/Moist/
# Wet are PRECIPITATION classes, not forest types (both ATTO forests are Moist, ~2100-
# 2400 mm/yr), so Caa=Dry is only a stand-in for the shorter campinarana stature.
PARAMS = {
    "Terra Firme": dict(pos="Pla", b0=1.2597, b1=0.5002, k=0.0109, color="#4269d0"),
    "Campinarana": dict(pos="Caa", b0=1.1064, b1=0.5002, k=0.0109, color="#e17c05"),
}

# Campinarana Michaelis-Menten H-D, calibrated to LOCAL white-sand structure.
# Anchor: Targhetta, Kesselmeier & Wittmann (2015), Folia Geobot. 50:185-205 — a
# campinarana inventory at the Uatuma SDR right next to the ATTO tower (same ATTO
# project): measured mean H = 13.1 m (1,849 trees, DBH>=10 cm), canopy ceiling ~22 m.
# Form H = Hmax*D/(b1+D): Michaelis-Menten was the best-fit form for campinarana in the
# Roraima oligotrophic-forest H-D study (Modelos alometricos... florestas oligotroficas,
# 2024), where campinarana's asymptote is distinct from (and far below) terra firme, and
# general/pantropical curves overestimate white-sand height by up to ~106%. Hmax is set
# from the local ceiling; b1 is pinned so H(D_ref) = H_ref (local community mean height
# at its approx mean DBH). Validated: over a simulated >=10 cm reverse-J population this
# recovers mean H ~13 m; over our DBH>=20 inventory mean ~16 m, max ~21 m (<= ceiling).
# TUNE / REPLACE when local H-D pairs arrive (ATTO/MAUA group) or Villa Zegarra (2017) /
# Woortmann et al. (2018) harvest data becomes available.
CAMPINARANA_MM = dict(Hmax=24.0, D_ref=18.0, H_ref=13.1)
_mm_b1 = CAMPINARANA_MM["Hmax"] * CAMPINARANA_MM["D_ref"] / CAMPINARANA_MM["H_ref"] \
    - CAMPINARANA_MM["D_ref"]

# Woortmann et al. (2018)-style correction of the terra-firme curve for comparison:
# H_camp = WOORTMANN_F * H_chave(D). A single stature factor fixes the MEAN but keeps the
# terra-firme curvature, so the largest trees still overshoot the campinarana ceiling
# (that is exactly why "mm" — with a real asymptote — is preferred). F is pinned so the
# scaled-Chave mean matches the "mm" mean over the campinarana inventory (set at runtime).
WOORTMANN_F = None  # computed in the data loop

# Height model driving each forest's surface area:
#   Terra Firme -> "chave" (validated, ~unbiased vs real heights)
#   Campinarana -> "mm"    (calibrated to local Targhetta 2015 structure; replaces the
#     earlier Feldpausch-Dry placeholder, which had no asymptote and pushed the largest
#     stems to an unphysical ~32 m. "feld" and "woort" kept as comparison columns.)
HEIGHT_MODEL = {"Terra Firme": "chave", "Campinarana": "mm"}

# Crown / total-woody surface area.
#   "chambers"    -> total woody = Chambers 2004 A_s(DBH); crown = A_s - trunk frustum.
#   "placeholder" -> crown = CROWN_PLACEHOLDER x stem (legacy; fixes crown share at 60%).
# Terra Firme uses Chambers (validated: its implied crown/trunk ~1.38 vs the 1.5x guess,
# total woody ~17.5k m²/ha inside the Chambers 17-21k benchmark). Campinarana stays on the
# placeholder because Chambers is height-blind and over-predicts crown for stunted white-
# sand trees (implied crown/trunk ~2.9) — see chambers_total_sa() caveat and crown_report().
CROWN_PLACEHOLDER = 1.5
CROWN_MODEL = {"Terra Firme": "chambers", "Campinarana": "placeholder"}

# Chave (2014) E environmental-stress grid (2.5 arc-min ≈ 5 km), sampled bilinearly.
E_NC = Path("Tree_data/ATTO/pantropical_allometry/pantropical_allometry/E.nc")

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.labelsize": 11, "axes.spines.top": False, "axes.spines.right": False,
})

BOX_STYLE = dict(patch_artist=True, showmeans=True, widths=0.55,
                 medianprops=dict(color="black", lw=2),
                 meanprops=dict(marker="^", markerfacecolor="white",
                                markeredgecolor="black", markersize=9))
BOX_LEGEND = [
    Line2D([0], [0], color="black", lw=2, label="Median"),
    Line2D([0], [0], marker="^", color="w", markerfacecolor="white",
           markeredgecolor="black", markersize=9, label="Mean"),
    Line2D([0], [0], color="0.6", lw=8, alpha=0.4, label="IQR (mid 50%)"),
]

# --------------------------------------------------------------- E sampling
def sample_E(lons, lats):
    """Bilinear-sample the Chave (2014) E parameter from E.nc at lon/lat points.

    Mirrors Chave's readlayers.r (raster::extract, method='bilinear'). Returns
    NaN where coordinates are missing; callers fill those per forest."""
    import xarray as xr
    lons = np.asarray(lons, float)
    lats = np.asarray(lats, float)
    out = np.full(lons.shape, np.nan)
    ok = np.isfinite(lons) & np.isfinite(lats)
    if ok.any():
        with xr.open_dataset(E_NC) as ds:
            da = ds["layer"].sel(  # small window around the points (latitude descends)
                longitude=slice(lons[ok].min() - 0.5, lons[ok].max() + 0.5),
                latitude=slice(lats[ok].max() + 0.5, lats[ok].min() - 0.5),
            ).sortby("latitude")
            out[ok] = da.interp(
                longitude=xr.DataArray(lons[ok], dims="p"),
                latitude=xr.DataArray(lats[ok], dims="p"),
                method="linear",
            ).values
    return out


def _stem_sa(H_m, r_bottom_cm, r_top_cm):
    """Lateral area of the truncated-cone stem (m²); radii given in cm."""
    return H_m * np.pi * (r_bottom_cm / 100 + r_top_cm / 100)


def chambers_total_sa(dbh_cm):
    """Chambers et al. (2004, Ecol. Appl. 14:S72-S88), Eq. 10 — TOTAL woody surface area
    (bole + branches, summed) as a function of DBH, for central-Amazon terra firme:

        log10(A_s) = -0.105 - 0.686 L + 2.208 L^2 - 0.627 L^3,   L = log10(DBH cm)

    A_s in m²; r²adj = 0.93, 315 harvested trees near Manaus. Applied over their inventory
    it gives a stem area index of 1.7 (= 17,000 m²/ha, >10 cm DBH) — the field benchmark.
    This is a cheap, independent estimate of total woody area (and, via A_s - trunk, of the
    crown/branch share), replacing the arbitrary crown = 1.5x-stem placeholder.

    CAVEAT: A_s depends on DBH ALONE (height-blind). It is derived on terra firme, so it is
    only appropriate for Terra Firme here; for the stunted Campinarana it over-predicts
    crown (a same-DBH white-sand tree is much shorter) and must be treated as an upper
    bound, not adopted."""
    L = np.log10(np.asarray(dbh_cm, float))
    return 10 ** (-0.105 - 0.686 * L + 2.208 * L ** 2 - 0.627 * L ** 3)


# ----------------------------------------------------------------------- data
raw = pd.read_excel(XLSX)
raw["E"] = sample_E(raw["LON"].values, raw["LAT"].values)   # Chave E per tree

forests = {}
for name, p in PARAMS.items():
    d = raw[raw["POS"] == p["pos"]].copy()
    if LIVE_ONLY:
        d = d[d["STATUS"] == "live"]
    d["E"] = d["E"].fillna(d["E"].median())     # rare blank-coordinate rows
    d["r_bottom_cm"] = d["DBH"] / 2
    d["r_top_cm"] = TAPER * d["r_bottom_cm"]

    # candidate height models; HEIGHT_MODEL[name] selects the one used
    d["H_feld"] = np.exp(p["b0"] + p["b1"] * np.log(d["DBH"]) + p["k"])
    d["H_chave"] = np.exp(0.893 - d["E"] + 0.760 * np.log(d["DBH"])
                          - 0.0340 * np.log(d["DBH"]) ** 2)
    # Michaelis-Menten (campinarana, local calibration); harmless for TF (unused there)
    d["H_mm"] = CAMPINARANA_MM["Hmax"] * d["DBH"] / (_mm_b1 + d["DBH"])
    _sel = {"chave": "H_chave", "feld": "H_feld", "mm": "H_mm"}[HEIGHT_MODEL[name]]
    d["H_m"] = d[_sel]

    # surface area under the selected model, plus a companion column per model
    d["SA_stem_m2"] = _stem_sa(d["H_m"], d["r_bottom_cm"], d["r_top_cm"])
    d["SA_stem_feld"] = _stem_sa(d["H_feld"], d["r_bottom_cm"], d["r_top_cm"])
    d["SA_stem_chave"] = _stem_sa(d["H_chave"], d["r_bottom_cm"], d["r_top_cm"])
    d["SA_stem_mm"] = _stem_sa(d["H_mm"], d["r_bottom_cm"], d["r_top_cm"])
    d["BA_m2"] = np.pi * (d["DBH"] / 200) ** 2

    # crown / total woody: Chambers total (bole+branch) vs the 1.5x-stem placeholder
    d["SA_total_chambers"] = chambers_total_sa(d["DBH"])
    d["SA_crown_chambers"] = (d["SA_total_chambers"] - d["SA_stem_m2"]).clip(lower=0)
    d["SA_crown_placeholder"] = CROWN_PLACEHOLDER * d["SA_stem_m2"]
    d["SA_crown_m2"] = (d["SA_crown_chambers"] if CROWN_MODEL[name] == "chambers"
                        else d["SA_crown_placeholder"])
    d["SA_woody_m2"] = d["SA_stem_m2"] + d["SA_crown_m2"]   # trunk + crown (total woody)
    forests[name] = d

# Woortmann et al. (2018)-style scaled-Chave comparison for campinarana: pin the stature
# factor so its mean matches the calibrated MM mean over the inventory (see WOORTMANN_F).
if "Campinarana" in forests:
    _dc = forests["Campinarana"]
    WOORTMANN_F = _dc["H_mm"].mean() / _dc["H_chave"].mean()
    _dc["H_woort"] = WOORTMANN_F * _dc["H_chave"]

names = list(forests.keys())
colors = [PARAMS[n]["color"] for n in names]
n_trees_total = sum(len(d) for d in forests.values())
n_plots = {n: forests[n]["CODE"].nunique() for n in names}
n_plots_total = sum(n_plots.values())
status_note = "live stems only" if LIVE_ONLY else "all stems (live + dead)"


def forest_legend():
    return [Line2D([0], [0], marker="s", color="w", markerfacecolor=c,
                   markersize=11, label=n) for n, c in zip(names, colors)]


def impact_report():
    """Print how the height-model choice changes stem surface area (Feld vs Chave-E)."""
    print("\n=== Height model per forest ===")
    for n in names:
        print(f"  {n:12s}: {HEIGHT_MODEL[n]:5s}   mean E = {forests[n]['E'].mean():+.4f}")
    rows = []
    for n in names:
        d = forests[n]
        area_ha = n_plots[n] * PLOT_SIZE_M2 / 10_000
        for label, hcol, sacol in [("Feldpausch", "H_feld", "SA_stem_feld"),
                                    ("Chave-E", "H_chave", "SA_stem_chave"),
                                    ("MM-local", "H_mm", "SA_stem_mm")]:
            rows.append(dict(Forest=n, Height=label, Used=(HEIGHT_MODEL[n] ==
                             {"H_feld": "feld", "H_chave": "chave", "H_mm": "mm"}[hcol]),
                             H_mean_m=round(d[hcol].mean(), 1),
                             SA_total_m2=round(d[sacol].sum()),
                             SA_m2_per_ha=round(d[sacol].sum() / area_ha)))
    print("\n=== Stem surface area under each height model ===")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\n=== Change Feldpausch -> Chave-E (per forest) ===")
    for n in names:
        sf = forests[n]["SA_stem_feld"].sum()
        sc = forests[n]["SA_stem_chave"].sum()
        print(f"  {n:12s}: {sf:>8,.0f} -> {sc:>8,.0f} m²  ({100 * (sc / sf - 1):+5.1f}%)"
              f"   [pipeline uses: {HEIGHT_MODEL[n]}]")
    campinarana_height_report()


def campinarana_height_report():
    """Campinarana height models vs the LOCAL anchor (Targhetta et al. 2015, Uatuma/ATTO:
    mean H 13.1 m at DBH>=10 cm, canopy ceiling ~22 m). Shows why the calibrated
    Michaelis-Menten ("mm") beats both the old Feldpausch placeholder and a Woortmann-
    style single-factor correction of the terra-firme curve."""
    if "Campinarana" not in forests:
        return
    d = forests["Campinarana"]
    print("\n=== Campinarana height models vs local anchor "
          "(Targhetta 2015: mean 13.1 m @>=10cm, ceiling ~22 m) ===")
    print(f"  inventory: n={len(d)}, DBH {d['DBH'].min():.0f}-{d['DBH'].max():.0f} cm "
          f"(mean {d['DBH'].mean():.1f}); note our threshold is DBH>=20 cm, so the mean "
          f"H should sit ABOVE 13.1 m,\n  with the tallest stems still <= ~22 m ceiling.")
    print(f"  Michaelis-Menten calibration: Hmax={CAMPINARANA_MM['Hmax']:.0f}, "
          f"b1={_mm_b1:.2f}  |  Woortmann stature factor F={WOORTMANN_F:.3f}")
    cols = [("Feldpausch (old placeholder)", "H_feld"),
            ("Chave-E (terra-firme curve)", "H_chave"),
            ("Michaelis-Menten (USED)", "H_mm"),
            ("Woortmann scaled-Chave", "H_woort")]
    print(f"  {'model':30s} {'mean':>6} {'p95':>6} {'max':>6}   ceiling check")
    for label, c in cols:
        h = d[c]
        flag = "ok (<=22)" if h.max() <= 22.5 else f"OVERSHOOT (max {h.max():.0f} m)"
        print(f"  {label:30s} {h.mean():6.1f} {h.quantile(0.95):6.1f} "
              f"{h.max():6.1f}   {flag}")
    campinarana_sa_band()


# Targhetta et al. (2015) campinarana mean height and its spread (m), used to propagate
# the stature (calibration) uncertainty into the reported campinarana surface area.
TARGHETTA_MEAN_H, TARGHETTA_SD_H = 13.1, 2.6


def campinarana_mm_height(dbh, h_ref, hmax=None, d_ref=None):
    """Michaelis-Menten campinarana height for a given stature anchor h_ref (m).
    hmax/d_ref default to the CAMPINARANA_MM calibration; b1 is re-derived from h_ref."""
    hmax = CAMPINARANA_MM["Hmax"] if hmax is None else hmax
    d_ref = CAMPINARANA_MM["D_ref"] if d_ref is None else d_ref
    b1 = hmax * d_ref / h_ref - d_ref
    return hmax * dbh / (b1 + dbh)


def campinarana_sa_band():
    """Fold the stature/height-model uncertainty into the campinarana stem-SA estimate.

    Campinarana stature is the dominant unknown: the MM curve is calibrated to Targhetta
    (2015)'s summary mean (13.1 +/- 2.6 m). Propagate that anchor spread by recalibrating
    MM at h_ref = mean +/- SD (ceiling Hmax fixed — it is better constrained), giving a
    low/central/high stem-SA band. Chave-E is excluded (fails the ~22 m ceiling); the old
    Feldpausch placeholder is printed for reference."""
    if "Campinarana" not in forests:
        return
    d = forests["Campinarana"]
    area_ha = n_plots["Campinarana"] * PLOT_SIZE_M2 / 10_000

    def sa_ha(h_ref):
        H = campinarana_mm_height(d["DBH"], h_ref)
        return _stem_sa(H, d["r_bottom_cm"], d["r_top_cm"]).sum() / area_ha, H.mean()

    lo_h, ce_h, hi_h = (TARGHETTA_MEAN_H - TARGHETTA_SD_H, TARGHETTA_MEAN_H,
                        TARGHETTA_MEAN_H + TARGHETTA_SD_H)
    (lo, lo_mh), (ce, ce_mh), (hi, hi_mh) = sa_ha(lo_h), sa_ha(ce_h), sa_ha(hi_h)
    feld = d["SA_stem_feld"].sum() / area_ha
    half = (hi - lo) / 2
    print("\n=== Campinarana stem-SA band (stature anchor 13.1 ± 2.6 m, Targhetta 2015) ===")
    print(f"  low  (H_ref {lo_h:.1f} m, mean H {lo_mh:4.1f}): {lo:5,.0f} m²/ha")
    print(f"  MID  (H_ref {ce_h:.1f} m, mean H {ce_mh:4.1f}): {ce:5,.0f} m²/ha  <- reported")
    print(f"  high (H_ref {hi_h:.1f} m, mean H {hi_mh:4.1f}): {hi:5,.0f} m²/ha")
    print(f"  => campinarana main-stem SA = {ce:,.0f} ± {half:,.0f} m²/ha "
          f"(±{100*half/ce:.0f}%)   [Feldpausch placeholder ref: {feld:,.0f}]")
    crown_report()


def crown_report():
    """Crown / total-woody surface area: Chambers 2004 total-woody allometry vs the legacy
    crown = 1.5x-stem placeholder. Chambers gives total woody (bole+branch) from DBH, so
    crown = A_s - trunk. For Terra Firme (central-Amazon terra firme, where Chambers was
    fit) this is a genuine independent estimate; for Campinarana it is height-blind and
    over-predicts crown (upper bound only)."""
    print("\n=== Crown / total-woody surface area: Chambers 2004 vs 1.5x placeholder ===")
    print(f"  {'forest':12s} {'trunk/ha':>9} {'crown/tr':>9} {'total/ha':>9}   method")
    for n in names:
        d = forests[n]
        area_ha = n_plots[n] * PLOT_SIZE_M2 / 10_000
        trunk = d["SA_stem_m2"].sum()
        ch_tot = d["SA_total_chambers"].sum()
        ph_tot = (d["SA_stem_m2"] + d["SA_crown_placeholder"]).sum()
        ch_ratio = (d["SA_crown_chambers"].sum()) / trunk
        used = CROWN_MODEL[n]
        print(f"  {n:12s} {trunk/area_ha:9,.0f}")
        print(f"      Chambers total-woody : crown/trunk {ch_ratio:4.2f}  "
              f"total {ch_tot/area_ha:6,.0f} /ha   [{'USED' if used=='chambers' else 'ref'}]")
        print(f"      1.5x placeholder     : crown/trunk 1.50  "
              f"total {ph_tot/area_ha:6,.0f} /ha   [{'USED' if used=='placeholder' else 'ref'}]")
    print("  Terra Firme: Chambers crown/trunk ~1.38 ~= the 1.5x guess, total ~17.5k/ha "
          "inside the 17-21k benchmark -> placeholder validated; Chambers adopted.")
    print("  Campinarana: Chambers is height-blind (crown/trunk ~2.9 is implausible for a "
          "stunted forest) -> kept on placeholder; crown remains the open approximation.")
    terrafirme_height_band()


# Height-model biases vs 523 measured Amazon heights (validate_height.py, pred - measured):
# Chave-E +6.7% (high), Feldpausch Guyana-Moist -8.5% (low). They straddle the truth, so
# the two models bracket a band and their midpoint is ~unbiased (-0.9%).
TF_HEIGHT_BIAS = {"Chave-E": +0.067, "Feldpausch": -0.085}


def terrafirme_height_band():
    """Fold the height-MODEL uncertainty into the Terra Firme surface area. Unlike the
    Campinarana stature band (one model, anchor uncertainty), TF's dominant uncertainty is
    the model choice: Chave-E (used, validated best but ~+7% high) vs Feldpausch Guyana-
    Moist (~-8% low). They straddle 523 measured heights, so they bracket the band and the
    midpoint is ~unbiased. KEY: because TF total woody = Chambers A_s(DBH) is height-blind,
    the height choice only moves the TRUNK/CROWN split — the total-woody number is invariant."""
    if "Terra Firme" not in forests:
        return
    d = forests["Terra Firme"]
    area_ha = n_plots["Terra Firme"] * PLOT_SIZE_M2 / 10_000
    trunk_lo = d["SA_stem_feld"].sum() / area_ha      # Feldpausch (low)
    trunk_hi = d["SA_stem_chave"].sum() / area_ha      # Chave-E (used, high)
    mid = (trunk_lo + trunk_hi) / 2
    half = (trunk_hi - trunk_lo) / 2
    total = d["SA_total_chambers"].sum() / area_ha     # Chambers, height-invariant
    print("\n=== Terra Firme height-model band (Feldpausch low <-> Chave-E high) ===")
    print(f"  main-stem SA  Feldpausch (-8% low): {trunk_lo:6,.0f} m2/ha")
    print(f"                Chave-E   (+7% high, USED): {trunk_hi:6,.0f} m2/ha")
    print(f"  => least-biased midpoint = {mid:,.0f} +/- {half:,.0f} m2/ha (+/-{100*half/mid:.0f}%);"
          f" Chave-E as used sits +{100*(trunk_hi/mid-1):.0f}% above it")
    print(f"  Total woody is Chambers-pinned at {total:,.0f} m2/ha REGARDLESS of height model")
    print(f"  (height only shifts the split: crown = {total-trunk_hi:,.0f}/ha at Chave-E "
          f"vs {total-trunk_lo:,.0f}/ha at Feldpausch).")


# ============================================================ Fig 1: plot data
def fig_plot_data():
    fig, (axh, axc) = plt.subplots(1, 2, figsize=(13, 5.2))

    dbh_max = max(d["DBH"].max() for d in forests.values())
    bins = np.arange(20, dbh_max + 10, 10)
    for n, d in forests.items():
        axh.hist(d["DBH"], bins=bins, color=PARAMS[n]["color"], alpha=0.55,
                 edgecolor="white", linewidth=0.6, label=n)
        axh.axvline(d["DBH"].median(), color=PARAMS[n]["color"], ls="--", lw=1.5)
    axh.set_xlabel("DBH (cm)")
    axh.set_ylabel("Number of trees")
    axh.set_title("Measured stem sizes (DBH ≥ 20 cm)")
    axh.legend(handles=forest_legend(), frameon=False)
    axh.grid(axis="y", alpha=0.3)
    axh.text(0.97, 0.72, "dashed = median DBH", transform=axh.transAxes,
             ha="right", fontsize=9, color="0.35")

    order, vals, cols = [], [], []
    for n, d in forests.items():
        g = d.groupby("CODE").size().sort_index()
        order += list(g.index)
        vals += list(g.values)
        cols += [PARAMS[n]["color"]] * len(g)
    axc.bar(range(len(order)), vals, color=cols, edgecolor="black", linewidth=0.5)
    axc.set_xticks(range(len(order)))
    axc.set_xticklabels(order, rotation=90, fontsize=8)
    axc.set_ylabel("Stems per plot")
    axc.set_title("Sampling design: stems per plot")
    axc.legend(handles=forest_legend(),
               title=f"{n_plots[names[0]]} + {n_plots[names[1]]} plots", frameon=False)
    axc.grid(axis="y", alpha=0.3)

    fig.suptitle(f"Plot inventory — {n_trees_total} trees across {n_plots_total} plots "
                 f"({status_note})", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTDIR / "fig1_plot_data.png")
    return fig


# ====================================================== Fig 2: height (Step 1)
def fig_height():
    fig, (axc, axb) = plt.subplots(1, 2, figsize=(13, 5.2),
                                   gridspec_kw={"width_ratios": [1.5, 1]})

    for n, d in forests.items():
        p = PARAMS[n]
        axc.scatter(d["DBH"], d["H_m"], s=16, alpha=0.30, color=p["color"])
        dd = np.linspace(20, d["DBH"].max(), 200)
        if HEIGHT_MODEL[n] == "chave":
            E = d["E"].median()
            hh = np.exp(0.893 - E + 0.760 * np.log(dd) - 0.0340 * np.log(dd) ** 2)
            lab = f"{n} — Chave-E"
        elif HEIGHT_MODEL[n] == "mm":
            hh = CAMPINARANA_MM["Hmax"] * dd / (_mm_b1 + dd)
            lab = f"{n} — Michaelis-Menten (local)"
        else:
            hh = np.exp(p["b0"] + p["b1"] * np.log(dd) + p["k"])
            lab = f"{n} — Feldpausch"
        axc.plot(dd, hh, color=p["color"], lw=2.6, label=lab)
    # local campinarana anchor (Targhetta et al. 2015, Uatuma/ATTO)
    axc.axhline(22, color=PARAMS["Campinarana"]["color"], ls=":", lw=1.5, alpha=0.8)
    axc.text(axc.get_xlim()[1], 22.3, "campinarana ceiling ~22 m (Targhetta 2015)",
             ha="right", va="bottom", fontsize=8,
             color=PARAMS["Campinarana"]["color"])
    axc.set_xlabel("DBH (cm)")
    axc.set_ylabel("Estimated height (m)")
    axc.set_title("Step 1 — Height from DBH (per-forest model)")
    axc.legend(frameon=False, loc="lower right")
    axc.grid(alpha=0.3)
    eqn = ("Terra Firme — Chave 2014:  "
           "$H=\\exp(0.893-E+0.760\\ln D-0.034\\ln^2\\! D)$\n"
           "Campinarana — Michaelis–Menten:  "
           f"$H=H_{{max}}\\,D/(b_1+D)$, $H_{{max}}={CAMPINARANA_MM['Hmax']:.0f}$, "
           f"$b_1={_mm_b1:.1f}$\n"
           "E per plot from E.nc · Caa MM calibrated to local Targhetta 2015 structure")
    axc.text(0.03, 0.97, eqn, transform=axc.transAxes, va="top", fontsize=8.5,
             bbox=dict(boxstyle="round", fc="white", ec="0.7"))

    bp = axb.boxplot([forests[n]["H_m"] for n in names], labels=names, **BOX_STYLE)
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.6)
    axb.set_ylabel("Estimated height (m)")
    axb.set_title("Resulting height distribution")
    axb.grid(axis="y", alpha=0.3)
    axb.legend(handles=BOX_LEGEND, fontsize=9, loc="upper right")

    fig.tight_layout()
    fig.savefig(OUTDIR / "fig2_height.png")
    return fig


# ==================================================== Fig 3: geometry (Step 2)
def fig_geometry():
    fig, (axs, axl) = plt.subplots(1, 2, figsize=(13, 5.4),
                                   gridspec_kw={"width_ratios": [1, 1.3]})

    # --- schematic of the truncated cone (not to scale) ---
    rb, rt, H = 1.0, TAPER, 4.2
    trunk = Polygon([(-rb, 0), (rb, 0), (rt, H), (-rt, H)],
                    closed=True, facecolor="#c9d4ef", edgecolor="#4269d0", lw=2)
    axs.add_patch(trunk)
    axs.annotate("", xy=(rb, -0.15), xytext=(-rb, -0.15),
                 arrowprops=dict(arrowstyle="<->", color="black"))
    axs.text(0, -0.5, "diameter = DBH  →  $r_{bottom}=DBH/2$", ha="center", fontsize=10)
    axs.annotate("", xy=(rt, H + 0.15), xytext=(-rt, H + 0.15),
                 arrowprops=dict(arrowstyle="<->", color="black"))
    axs.text(0, H + 0.4, f"$r_{{top}} = {TAPER}\\times r_{{bottom}}$", ha="center", fontsize=10)
    axs.annotate("", xy=(rb + 0.55, H), xytext=(rb + 0.55, 0),
                 arrowprops=dict(arrowstyle="<->", color="0.4"))
    axs.text(rb + 0.72, H / 2, "$H$\n(Step 1)", va="center", fontsize=10, color="0.3")
    axs.set_xlim(-2.1, 2.4)
    axs.set_ylim(-1.1, H + 1.1)
    axs.set_aspect("equal")
    axs.axis("off")
    axs.set_title("Step 2 — Trunk as a truncated cone")
    axs.text(0.5, -0.02,
             r"Lateral area $= \pi\,(r_{bottom}+r_{top})\times H$",
             transform=axs.transAxes, ha="center", fontsize=11,
             bbox=dict(boxstyle="round", fc="#fff4e6", ec="#e17c05"))
    axs.text(0.99, 0.99, "not to scale", transform=axs.transAxes, ha="right",
             va="top", fontsize=8, color="0.5")

    # --- resulting SA vs DBH, log-log (shows the ~DBH^1.5 scaling) ---
    all_dbh = np.concatenate([forests[n]["DBH"].values for n in names])
    all_sa = np.concatenate([forests[n]["SA_stem_m2"].values for n in names])
    slope = np.polyfit(np.log(all_dbh), np.log(all_sa), 1)[0]
    for n, d in forests.items():
        axl.scatter(d["DBH"], d["SA_stem_m2"], s=18, alpha=0.5,
                    color=PARAMS[n]["color"], label=n)
    axl.set_xscale("log")
    axl.set_yscale("log")
    axl.set_xlabel("DBH (cm, log)")
    axl.set_ylabel("Main-stem surface area (m², log)")
    axl.set_title("Resulting main-stem area vs DBH")
    axl.legend(handles=forest_legend(), frameon=False, loc="lower right")
    axl.grid(which="both", alpha=0.3)
    axl.text(0.03, 0.95, f"power-law slope ≈ {slope:.2f}\n(area $\\propto DBH^{{1.5}}$)",
             transform=axl.transAxes, va="top", fontsize=10,
             bbox=dict(boxstyle="round", fc="white", ec="0.7"))

    fig.tight_layout()
    fig.savefig(OUTDIR / "fig3_geometry.png")
    return fig


# ================================================ Fig 4: final estimate (Step 3)
def fig_estimate():
    fig, (axd, axt) = plt.subplots(1, 2, figsize=(13, 5.4))

    # Per-tree main-stem area as mean with TWO error bars:
    #   grey/thin  = SD across all trees (per-tree spread)
    #   black/bold = SD across plot means (between-plot / stand-level spread)
    xpos = np.arange(len(names))
    m = [forests[n]["SA_stem_m2"].mean() for n in names]
    tree_sd = [forests[n]["SA_stem_m2"].std() for n in names]
    plot_sd = [forests[n].groupby("CODE")["SA_stem_m2"].mean().std() for n in names]
    axd.bar(xpos, m, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    axd.errorbar(xpos - 0.08, m, yerr=tree_sd, fmt="none", ecolor="0.35",
                 lw=1.5, capsize=11, capthick=1.5, alpha=0.9)
    axd.errorbar(xpos + 0.08, m, yerr=plot_sd, fmt="none", ecolor="black",
                 lw=3, capsize=5, capthick=3)
    axd.set_xticks(xpos)
    axd.set_xticklabels(names)
    axd.set_ylabel("Main-stem area per tree (m²)")
    axd.set_title("Step 3 — Per-tree main-stem surface area (mean ± SD)")
    axd.grid(axis="y", alpha=0.3)
    axd.legend(handles=[
        Line2D([0], [0], color="0.35", lw=1.5, label="SD across trees"),
        Line2D([0], [0], color="black", lw=3, label="SD across plots"),
    ], fontsize=9, loc="upper right")
    for xi, mm, ts, ps in zip(xpos, m, tree_sd, plot_sd):
        axd.text(xi, mm + ts, f"{mm:.1f} m²\n±{ts:.1f} tree / ±{ps:.1f} plot",
                 ha="center", va="bottom", fontsize=8)

    # Total = sum of plot totals; plots (equal 1200 m² area) are the replicate.
    # Between-plot SD propagates to the sum as SD(plot total) * sqrt(n_plots).
    totals, tot_sd = [], []
    for n in names:
        plot_tot = forests[n].groupby("CODE")["SA_stem_m2"].sum()
        totals.append(plot_tot.sum())
        tot_sd.append(plot_tot.std() * np.sqrt(len(plot_tot)))
    bars = axt.bar(names, totals, yerr=tot_sd, capsize=8, color=colors, alpha=0.85,
                   edgecolor="black", linewidth=0.8,
                   error_kw=dict(ecolor="black", lw=1.5))
    axt.set_ylabel("Total main-stem surface area (m²)")
    axt.set_title("Total main-stem area per forest (± between-plot SD)")
    axt.grid(axis="y", alpha=0.3)
    for bar, n, tot, sd in zip(bars, names, totals, tot_sd):
        per_ha = tot / (n_plots[n] * PLOT_SIZE_M2 / 10_000)
        axt.text(bar.get_x() + bar.get_width() / 2, tot + sd,
                 f"{tot:,.0f} ± {sd:,.0f} m²\n({per_ha:,.0f} m²/ha*)",
                 ha="center", va="bottom", fontsize=10)

    fig.suptitle("Main-stem surface-area estimate  (crown estimated separately)",
                 fontsize=15, fontweight="bold")
    fig.text(0.5, 0.005,
             f"* per-ha — plot area: {PLOT_SIZE_M2:.0f} m². "
             f"Total ± SD = between-plot variability propagated to the sum "
             f"(SD of plot totals × √n_plots). Based on {status_note}.",
             ha="center", fontsize=9, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUTDIR / "fig4_estimate.png")
    return fig


# ========================================== Fig 5: estimation bandwidth (mean ± SD)
def fig_bandwidth():
    """Mean ± SD of DBH, height and main-stem area — the bandwidth of the estimates.

    (a) per-plot DBH (within-plot SD);  (b/c/d) per-forest DBH / height / area
    with TWO error bars: grey/thin = SD across all trees (per-tree spread),
    black/bold = SD across plot means (between-plot / stand-level spread).
    """
    fig, ((ax_dbh_plot, ax_dbh),
          (ax_h, ax_sa)) = plt.subplots(2, 2, figsize=(13, 10))

    # (a) per-plot mean DBH ± within-plot SD (each bar = one plot)
    codes, means, stds, cols = [], [], [], []
    for n, d in forests.items():
        g = d.groupby("CODE")["DBH"]
        m, s = g.mean().sort_index(), g.std().sort_index()
        codes += list(m.index)
        means += list(m.values)
        stds += list(s.values)
        cols += [PARAMS[n]["color"]] * len(m)
    x = np.arange(len(codes))
    ax_dbh_plot.bar(x, means, yerr=stds, capsize=4, color=cols, alpha=0.85,
                    edgecolor="black", linewidth=0.6,
                    error_kw=dict(ecolor="black", lw=1.2))
    ax_dbh_plot.set_xticks(x)
    ax_dbh_plot.set_xticklabels(codes, rotation=90, fontsize=8)
    ax_dbh_plot.set_ylabel("DBH (cm)")
    ax_dbh_plot.set_title("(a) Per-plot mean DBH ± within-plot SD")
    ax_dbh_plot.grid(axis="y", alpha=0.3)
    ax_dbh_plot.legend(handles=forest_legend(), frameon=False)

    # (b/c/d) per-forest mean with two error bars (tree-level + across-plot SD)
    def forest_bar(ax, col, ylabel, title, unit):
        xpos = np.arange(len(names))
        m = [forests[n][col].mean() for n in names]
        tree_sd = [forests[n][col].std() for n in names]
        plot_sd = [forests[n].groupby("CODE")[col].mean().std() for n in names]
        ax.bar(xpos, m, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
        ax.errorbar(xpos - 0.08, m, yerr=tree_sd, fmt="none", ecolor="0.35",
                    lw=1.5, capsize=11, capthick=1.5, alpha=0.9)
        ax.errorbar(xpos + 0.08, m, yerr=plot_sd, fmt="none", ecolor="black",
                    lw=3, capsize=5, capthick=3)
        ax.set_xticks(xpos)
        ax.set_xticklabels(names)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
        for xi, mm, ts, ps in zip(xpos, m, tree_sd, plot_sd):
            ax.text(xi, mm + ts, f"{mm:.1f} {unit}\n±{ts:.1f} tree / ±{ps:.1f} plot",
                    ha="center", va="bottom", fontsize=8)

    forest_bar(ax_dbh, "DBH", "DBH (cm)", "(b) Per-forest mean DBH ± SD", "cm")
    forest_bar(ax_h, "H_m", "Height (m)", "(c) Per-forest mean height ± SD", "m")
    forest_bar(ax_sa, "SA_stem_m2", "Main-stem area per tree (m²)",
               "(d) Per-forest mean main-stem area ± SD", "m²")

    fig.legend(handles=[
        Line2D([0], [0], color="0.35", lw=1.5, label="SD across trees (per-tree spread)"),
        Line2D([0], [0], color="black", lw=3, label="SD across plots (between-plot spread)"),
    ], ncol=2, fontsize=10, loc="lower center", frameon=False,
        bbox_to_anchor=(0.5, 0.0))

    fig.suptitle(f"Estimation bandwidth — mean ± SD  ({status_note})",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 0.98))
    fig.savefig(OUTDIR / "fig5_bandwidth.png")
    return fig


# ================================== Fig 6: crown / total woody (Chambers vs placeholder)
def fig_crown():
    """Total woody surface area per ha (trunk + crown): Chambers 2004 total-woody allometry
    vs the legacy crown = 1.5x-stem placeholder, for both forests."""
    fig, ax = plt.subplots(figsize=(11, 6))

    # Chambers 2004 field benchmark (central-Amazon terra firme, >10 cm DBH)
    ax.axhspan(17_000, 21_000, color="#4269d0", alpha=0.08, zorder=0)
    ax.text(-0.45, 21_100, "Chambers 2004 benchmark 17–21k m²/ha (terra firme)",
            ha="left", va="bottom", fontsize=8.5, color="#4269d0")

    bar_w = 0.34
    x = np.arange(len(names))
    for i, n in enumerate(names):
        d = forests[n]
        area_ha = n_plots[n] * PLOT_SIZE_M2 / 10_000
        trunk = d["SA_stem_m2"].sum() / area_ha
        crown_ch = d["SA_crown_chambers"].sum() / area_ha
        crown_ph = d["SA_crown_placeholder"].sum() / area_ha
        col = PARAMS[n]["color"]
        xc, xp = x[i] - bar_w / 2 - 0.02, x[i] + bar_w / 2 + 0.02
        used_ch = CROWN_MODEL[n] == "chambers"
        for xb, crown, hatch, tag in [(xc, crown_ch, "//", "Chambers"),
                                      (xp, crown_ph, "..", "1.5×")]:
            ax.bar(xb, trunk, bar_w, color=col, edgecolor="black", linewidth=0.8)
            ax.bar(xb, crown, bar_w, bottom=trunk, color=col, alpha=0.4,
                   hatch=hatch, edgecolor="black", linewidth=0.8)
            is_used = (tag == "Chambers") == used_ch
            ax.text(xb, trunk + crown, f"{tag}\n{trunk + crown:,.0f}"
                    + ("\n(used)" if is_used else ""), ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold" if is_used else "normal")
        ax.text(x[i], -1600, f"trunk {trunk:,.0f} m²/ha", ha="center", fontsize=8,
                color="0.35")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("Total woody surface area (m²/ha)")
    ax.set_title("Step 4 — Crown / total woody: Chambers 2004 allometry vs 1.5× placeholder",
                 fontsize=13, fontweight="bold")
    ax.set_ylim(0, 24_000)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(handles=[
        Line2D([0], [0], marker="s", color="w", markerfacecolor="0.5", markersize=12,
               label="trunk frustum (Step 3)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="0.7", markersize=12,
               label="crown — Chambers (//)  vs  1.5× placeholder (··)"),
    ], frameon=False, loc="upper right")
    fig.text(0.5, 0.005,
             "Chambers is central-Amazon terra firme & DBH-only (height-blind): adopted for "
             "Terra Firme (crown/trunk 1.38 ≈ 1.5); for Campinarana it over-predicts crown "
             "(2.9) so the placeholder is kept.", ha="center", fontsize=8.5, color="0.4")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUTDIR / "fig6_crown.png")
    return fig


if __name__ == "__main__":
    impact_report()
    fig_plot_data()
    fig_height()
    fig_geometry()
    fig_estimate()
    fig_bandwidth()
    fig_crown()
    print(f"Saved 6 figures to {OUTDIR.resolve()}")
    plt.show()
