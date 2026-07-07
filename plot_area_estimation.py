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

# Height from DBH — two candidate models, validated in validate_height.py against
# real measured Amazon heights (Chave direct-harvest data):
#   "chave": Chave et al. 2014 pantropical, H = exp(0.893 - E + 0.760 lnD - 0.0340 lnD^2),
#            with E (environmental stress) sampled per plot from E.nc. Best fit to
#            measured central/Guyana-Shield heights (bias +0.4 m, RMSE 3.4 m).
#   "feld" : Feldpausch et al. 2011 regional, H = exp(b0 + b1 lnD + k).
# The Feldpausch b0 pair below is Guyana-Shield MOIST (TF) vs DRY (Caa) — but Dry/Moist/
# Wet are PRECIPITATION classes, not forest types (both ATTO forests are Moist, ~2100-
# 2400 mm/yr), so Caa=Dry is only a stand-in for the shorter campinarana stature.
PARAMS = {
    "Terra Firme": dict(pos="Pla", b0=1.2597, b1=0.5002, k=0.0109, color="#4269d0"),
    "Campinarana": dict(pos="Caa", b0=1.1064, b1=0.5002, k=0.0109, color="#e17c05"),
}

# Height model driving each forest's surface area:
#   Terra Firme -> "chave" (validated, ~unbiased vs real heights)
#   Campinarana -> "feld"  (UNVALIDATED placeholder: no white-sand tree exists in the
#     harvest data, and Chave-E can't separate it from TF because E is ~identical a few
#     km apart; keeps the shorter-tree behaviour until a real campinarana allometry is
#     sourced — see the deferred fresh-session todo.)
HEIGHT_MODEL = {"Terra Firme": "chave", "Campinarana": "feld"}

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

    # two candidate height models; HEIGHT_MODEL[name] selects the one used
    d["H_feld"] = np.exp(p["b0"] + p["b1"] * np.log(d["DBH"]) + p["k"])
    d["H_chave"] = np.exp(0.893 - d["E"] + 0.760 * np.log(d["DBH"])
                          - 0.0340 * np.log(d["DBH"]) ** 2)
    d["H_m"] = d["H_chave"] if HEIGHT_MODEL[name] == "chave" else d["H_feld"]

    # surface area under the selected model, plus a companion column per model
    d["SA_stem_m2"] = _stem_sa(d["H_m"], d["r_bottom_cm"], d["r_top_cm"])
    d["SA_stem_feld"] = _stem_sa(d["H_feld"], d["r_bottom_cm"], d["r_top_cm"])
    d["SA_stem_chave"] = _stem_sa(d["H_chave"], d["r_bottom_cm"], d["r_top_cm"])
    d["BA_m2"] = np.pi * (d["DBH"] / 200) ** 2
    forests[name] = d

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
                                    ("Chave-E", "H_chave", "SA_stem_chave")]:
            rows.append(dict(Forest=n, Height=label,
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
        else:
            hh = np.exp(p["b0"] + p["b1"] * np.log(dd) + p["k"])
            lab = f"{n} — Feldpausch"
        axc.plot(dd, hh, color=p["color"], lw=2.6, label=lab)
    axc.set_xlabel("DBH (cm)")
    axc.set_ylabel("Estimated height (m)")
    axc.set_title("Step 1 — Height from DBH (per-forest model)")
    axc.legend(frameon=False, loc="lower right")
    axc.grid(alpha=0.3)
    eqn = ("Terra Firme — Chave 2014:  "
           "$H=\\exp(0.893-E+0.760\\ln D-0.034\\ln^2\\! D)$\n"
           "Campinarana — Feldpausch 2011:  "
           "$H=\\exp(\\beta_0+\\beta_1\\ln D+\\kappa)$\n"
           "E sampled per plot from E.nc · Caa = unvalidated placeholder")
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


if __name__ == "__main__":
    impact_report()
    fig_plot_data()
    fig_height()
    fig_geometry()
    fig_estimate()
    fig_bandwidth()
    print(f"Saved 5 figures to {OUTDIR.resolve()}")
    plt.show()
