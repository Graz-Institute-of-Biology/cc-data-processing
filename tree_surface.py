import pandas as pd
import numpy as np

# Read Excel file
df = pd.read_excel(r'C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\Tree_data\ATTO\plots\JKI_AG-Waldlabor_ATTO_Faulhammer_.xlsx')

df_calc_tf = pd.DataFrame(columns=["NO", "DBH"])
df_calc_ca = pd.DataFrame(columns=["NO", "DBH"])

E_tf = -0.11351637
E_ca = -0.110835455

# Guyana Shield - Terra Firme [MOIST]
beta_zero_moist_tf = 1.2597
beta_one_moist_tf = 0.5002
kappa_moist_tf = 0.0109

# Guyana Shield - Campinarana [DRY]
beta_zero_moist_ca = 1.1064
beta_one_moist_ca = 0.5002
kappa_moist_ca = 0.0109

# Brazilian Shield - Terra Firme
# beta_zero_moist_tf = 1.1969
# beta_one_moist_tf = 0.4627
# kappa_moist_tf = 0.0109

# Brazilian Shield - Campinarana
# beta_zero_moist_ca = 1.0436
# beta_one_moist_ca = 0.4627
# kappa_moist_ca = 0.0109

# Display the first few rows
print(df.head())
print(df["POS"].unique())

# print(df["POS"] == "Pla")

tf_trees = df[df["POS"] == "Pla"]
ca_trees = df[df["POS"] == "Caa"]

print("Terra Firme Trees:")
print(tf_trees[["NO", "DBH"]])

df_calc_tf["NO"] = tf_trees["NO"]
df_calc_tf["DBH"] = tf_trees["DBH"]
df_calc_tf["Radius_bottom"] = tf_trees["DBH"] * 0.5
df_calc_tf["Radius_top"] = df_calc_tf["Radius_bottom"] *0.7
# df_calc_tf["Estimated_height_chaves"] = np.exp(0.893 - E_tf + 0.760*np.log(tf_trees["DBH"]) - 0.0340*(np.log(tf_trees["DBH"])**2)) # ln(H) = 0.893 - E +0.760*ln(D) - 0.0340*|ln(D)|²
df_calc_tf["Estimated_height_feldpausch"] = np.exp(beta_zero_moist_tf + beta_one_moist_tf * np.log(tf_trees["DBH"]) + kappa_moist_tf) # log(H) = beta_zero_moist + beta_one_moist log(DBH) + kappa_moist
# df_calc_tf["Estimated_surface_area_ch"] = df_calc_tf["Estimated_height_chaves"] * np.pi * (df_calc_tf["Radius_bottom"]/100 + df_calc_tf["Radius_top"]/100)
df_calc_tf["Estimated_surface_area_fp_main_stem"] = df_calc_tf["Estimated_height_feldpausch"] * np.pi * (df_calc_tf["Radius_bottom"]/100 + df_calc_tf["Radius_top"]/100)
df_calc_tf["Estimated_surface_area_fp_crown"] = df_calc_tf["Estimated_surface_area_fp_main_stem"] * 1.5
df_calc_tf["Estimated_surface_area_fp_total"] = df_calc_tf["Estimated_surface_area_fp_main_stem"] + df_calc_tf["Estimated_surface_area_fp_crown"]
print(df_calc_tf.sort_values("DBH"))
print("Total Estimated Surface Area (Terra Firme):", df_calc_tf["Estimated_surface_area_fp_total"].sum())


print("Campinarana Trees:")
print(ca_trees[["NO", "DBH"]])
df_calc_ca["NO"] = ca_trees["NO"]
df_calc_ca["DBH"] = ca_trees["DBH"]
df_calc_ca["Radius_bottom"] = df_calc_ca["DBH"] * 0.5
df_calc_ca["Radius_top"] = df_calc_ca["Radius_bottom"] *0.7
# df_calc_ca["Estimated_height_chaves"] = np.exp(0.893 - E_ca + 0.760*np.log(ca_trees["DBH"]) - 0.0340*(np.log(ca_trees["DBH"])**2)) # ln(H) = 0.893 - E +0.760*ln(D) - 0.0340*|ln(D)|²
df_calc_ca["Estimated_height_feldpausch"] = np.exp(beta_zero_moist_ca + beta_one_moist_ca * np.log(ca_trees["DBH"]) + kappa_moist_ca) # log(H ) = beta_zero_moist + beta_one_moist log(DBH) + kappa_moist
# df_calc_ca["Estimated_surface_area_ch"] = df_calc_ca["Estimated_height_chaves"] * np.pi * (df_calc_ca["Radius_bottom"]/100 + df_calc_ca["Radius_top"]/100)
df_calc_ca["Estimated_surface_area_fp_main_stem"] = df_calc_ca["Estimated_height_feldpausch"] * np.pi * (df_calc_ca["Radius_bottom"]/100 + df_calc_ca["Radius_top"]/100)
df_calc_ca["Estimated_surface_area_fp_crown"] = df_calc_ca["Estimated_surface_area_fp_main_stem"] * 1.5
df_calc_ca["Estimated_surface_area_fp_total"] = df_calc_ca["Estimated_surface_area_fp_main_stem"] + df_calc_ca["Estimated_surface_area_fp_crown"]
print(df_calc_ca.sort_values("DBH"))
print("Total Estimated Surface Area (Campinarana):", df_calc_ca["Estimated_surface_area_fp_total"].sum())


# ----------------------------------------------------------------------
# Summary statistics & forest comparison
# ----------------------------------------------------------------------

# Basal area per tree (m^2): pi * (DBH/2)^2, DBH given in cm -> divide by 200
df_calc_tf["Basal_area"] = np.pi * (df_calc_tf["DBH"] / 200) ** 2
df_calc_ca["Basal_area"] = np.pi * (df_calc_ca["DBH"] / 200) ** 2

# Area normalization. The inventory has MULTIPLE plots per forest (one per CODE),
# so each forest's ground area = (its plot count) x (single-plot area).
# NOTE: single-plot dimensions still to be confirmed against the field protocol.
PLOT_SIZE_M2 = 20 * 60             # confirmed plot dimensions: 20 m x 60 m = 1200 m^2
PLOT_AREA_HA = PLOT_SIZE_M2 / 10_000

n_plots_tf = tf_trees["CODE"].nunique()
n_plots_ca = ca_trees["CODE"].nunique()
print(f"\nPlots per forest -> Terra Firme: {n_plots_tf} | Campinarana: {n_plots_ca}")


def summarize(df, name, n_plots):
    """Per-forest summary of the derived height / surface-area estimates."""
    area_ha = n_plots * PLOT_AREA_HA
    h = df["Estimated_height_feldpausch"]
    sa = df["Estimated_surface_area_fp_total"]
    dbh = df["DBH"]
    return {
        "Forest": name,
        "n_plots": n_plots,
        "plot_area_ha": area_ha,
        "n_trees": len(df),
        "Stem_density_per_ha": len(df) / area_ha,
        "DBH_mean_cm": dbh.mean(),
        "DBH_std_cm": dbh.std(),
        "Height_mean_m": h.mean(),
        "Height_std_m": h.std(),
        "Height_CV_%": 100 * h.std() / h.mean(),
        "Height_min_m": h.min(),
        "Height_median_m": h.median(),
        "Height_max_m": h.max(),
        "SA_per_tree_mean_m2": sa.mean(),
        "SA_per_tree_std_m2": sa.std(),
        "SA_CV_%": 100 * sa.std() / sa.mean(),
        "SA_total_m2": sa.sum(),
        "SA_m2_per_ha": sa.sum() / area_ha,
        "Crown_share_%": 100 * df["Estimated_surface_area_fp_crown"].sum() / sa.sum(),
        "Basal_area_total_m2": df["Basal_area"].sum(),
        "Basal_area_m2_per_ha": df["Basal_area"].sum() / area_ha,
    }


summary = pd.DataFrame([summarize(df_calc_tf, "Terra Firme", n_plots_tf),
                        summarize(df_calc_ca, "Campinarana", n_plots_ca)]).set_index("Forest")
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
print("\n=== Summary statistics (pooled across all trees) ===")
print(summary.T)


# ----------------------------------------------------------------------
# Per-plot aggregation: the PLOT (CODE) is the unit of replication.
# Pooled tree-level SD (above) blends within- and between-plot variation;
# aggregating to plot means first gives the proper stand-level spread.
# ----------------------------------------------------------------------
df_calc_tf["CODE"] = tf_trees["CODE"]
df_calc_ca["CODE"] = ca_trees["CODE"]


def per_plot_stats(df):
    """Aggregate tree-level estimates to one row per plot (CODE).

    For DBH, height and surface area we keep BOTH the within-plot mean and
    the within-plot SD (spread among the trees in that single plot)."""
    g = df.groupby("CODE")
    return pd.DataFrame({
        "n_trees": g.size(),
        "DBH_mean_cm": g["DBH"].mean(),
        "DBH_std_cm": g["DBH"].std(),
        "Height_mean_m": g["Estimated_height_feldpausch"].mean(),
        "Height_std_m": g["Estimated_height_feldpausch"].std(),
        "SA_per_tree_mean_m2": g["Estimated_surface_area_fp_total"].mean(),
        "SA_per_tree_std_m2": g["Estimated_surface_area_fp_total"].std(),
        "SA_total_m2": g["Estimated_surface_area_fp_total"].sum(),
        "Basal_area_m2_per_ha": g["Basal_area"].sum() / PLOT_AREA_HA,
        "Stem_density_per_ha": g.size() / PLOT_AREA_HA,
    })


per_plot_tf = per_plot_stats(df_calc_tf)
per_plot_ca = per_plot_stats(df_calc_ca)
print("\n=== Per-plot values (Terra Firme) ===")
print(per_plot_tf)
print("\n=== Per-plot values (Campinarana) ===")
print(per_plot_ca)


def plot_level_summary(per_plot, name):
    """Mean +/- SD ACROSS plots (n = plot count), the stand-level statistic."""
    return pd.DataFrame({(name, "mean"): per_plot.mean(),
                         (name, "SD"): per_plot.std()})


plot_summary = pd.concat([plot_level_summary(per_plot_tf, "Terra Firme"),
                          plot_level_summary(per_plot_ca, "Campinarana")], axis=1)
print("\n=== Plot-level summary (mean ± SD across plots) ===")
print(plot_summary)


import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(df_calc_tf["Estimated_height_feldpausch"], bins=10, edgecolor='black', alpha=0.7)
axes[0].set_xlabel("Height (m)")
axes[0].set_ylabel("Frequency")
axes[0].set_title("Terra Firme - Height Distribution")
axes[0].grid(axis='y', alpha=0.3)

axes[1].hist(df_calc_ca["Estimated_height_feldpausch"], bins=10, edgecolor='black', alpha=0.7)
axes[1].set_xlabel("Height (m)")
axes[1].set_ylabel("Frequency")
axes[1].set_title("Campinarana - Height Distribution")
axes[1].grid(axis='y', alpha=0.3)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].scatter(df_calc_tf["DBH"], df_calc_tf["Estimated_height_feldpausch"], alpha=0.6)
axes[0].set_xlabel("DBH (cm)")
axes[0].set_ylabel("Height (m)")
axes[0].set_title("Terra Firme - Height vs DBH")
axes[0].grid(alpha=0.3)

axes[1].scatter(df_calc_ca["DBH"], df_calc_ca["Estimated_height_feldpausch"], alpha=0.6)
axes[1].set_xlabel("DBH (cm)")
axes[1].set_ylabel("Height (m)")
axes[1].set_title("Campinarana - Height vs DBH")
axes[1].grid(alpha=0.3)
plt.tight_layout()
fig, ax = plt.subplots(figsize=(10, 6))

ax.scatter(df_calc_tf["DBH"], df_calc_tf["Estimated_height_feldpausch"], alpha=0.6, label="Terra Firme", s=50)
ax.scatter(df_calc_ca["DBH"], df_calc_ca["Estimated_height_feldpausch"], alpha=0.6, label="Campinarana", s=50)
ax.set_xlabel("DBH (cm)")
ax.set_ylabel("Height (m)")
ax.set_title("Height vs DBH - Forest Comparison", fontsize=14)
ax.tick_params(axis='both', labelsize=11)
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()


# ----------------------------------------------------------------------
# Comparison plots: mean height / surface area (+/- SD) and distributions
# ----------------------------------------------------------------------
forests = ["Terra Firme", "Campinarana"]
colors = ["#4269d0", "#e17c05"]  # CVD-distinct categorical pair, fixed order
h_tf = df_calc_tf["Estimated_height_feldpausch"]
h_ca = df_calc_ca["Estimated_height_feldpausch"]
sa_tf = df_calc_tf["Estimated_surface_area_fp_total"]
sa_ca = df_calc_ca["Estimated_surface_area_fp_total"]

# Shared boxplot styling so the median line and mean marker are unambiguous
from matplotlib.lines import Line2D

BOX_STYLE = dict(patch_artist=True, showmeans=True, widths=0.5,
                 medianprops=dict(color="black", lw=2),
                 meanprops=dict(marker="^", markerfacecolor="white",
                                markeredgecolor="black", markersize=9))
box_handles = [
    Line2D([0], [0], color="black", lw=2, label="Median"),
    Line2D([0], [0], marker="^", color="w", markerfacecolor="white",
           markeredgecolor="black", markersize=9, label="Mean"),
    Line2D([0], [0], color="0.6", lw=8, alpha=0.4, label="IQR (mid 50%)"),
]

# --- Figure: mean height +/- SD (bar) and height distribution (box) ---
fig, (ax_bar, ax_box) = plt.subplots(1, 2, figsize=(12, 6))

h_means = [h_tf.mean(), h_ca.mean()]
h_stds = [h_tf.std(), h_ca.std()]
bars = ax_bar.bar(forests, h_means, yerr=h_stds, capsize=8, color=colors,
                  alpha=0.85, edgecolor="black", linewidth=0.8,
                  error_kw=dict(ecolor="black", lw=1.5))
ax_bar.set_ylabel("Estimated height (m)")
ax_bar.set_title("Mean estimated tree height ± SD")
ax_bar.grid(axis="y", alpha=0.3)
for bar, m, s in zip(bars, h_means, h_stds):
    ax_bar.text(bar.get_x() + bar.get_width() / 2, m + s + 0.2,
                f"{m:.1f} ± {s:.1f} m", ha="center", va="bottom", fontsize=10)

bp = ax_box.boxplot([h_tf, h_ca], labels=forests, **BOX_STYLE)
for patch, c in zip(bp["boxes"], colors):
    patch.set_facecolor(c)
    patch.set_alpha(0.6)
ax_box.set_ylabel("Estimated height (m)")
ax_box.set_title("Height distribution per tree")
ax_box.grid(axis="y", alpha=0.3)
ax_box.legend(handles=box_handles, loc="upper right", fontsize=9)
plt.tight_layout()

# --- Figure: mean surface area/tree +/- SD and total SA split stem/crown ---
fig, (ax_sa, ax_stack) = plt.subplots(1, 2, figsize=(12, 6))

# Mean surface area per tree +/- SD (pooled across all trees in the forest).
# NB: SA is right-skewed (~DBH^1.5), so the SD is large relative to the mean;
# it reflects the true spread of per-tree estimates rather than a symmetric band.
sa_means = [sa_tf.mean(), sa_ca.mean()]
sa_stds = [sa_tf.std(), sa_ca.std()]
bars = ax_sa.bar(forests, sa_means, yerr=sa_stds, capsize=8, color=colors,
                 alpha=0.85, edgecolor="black", linewidth=0.8,
                 error_kw=dict(ecolor="black", lw=1.5))
ax_sa.set_ylabel("Surface area per tree (m²)")
ax_sa.set_title("Mean surface area per tree ± SD")
ax_sa.grid(axis="y", alpha=0.3)
for bar, m, s in zip(bars, sa_means, sa_stds):
    ax_sa.text(bar.get_x() + bar.get_width() / 2, m + s + 1,
               f"{m:.1f} ± {s:.1f} m²", ha="center", va="bottom", fontsize=10)

stem_tot = [df_calc_tf["Estimated_surface_area_fp_main_stem"].sum(),
            df_calc_ca["Estimated_surface_area_fp_main_stem"].sum()]
crown_tot = [df_calc_tf["Estimated_surface_area_fp_crown"].sum(),
             df_calc_ca["Estimated_surface_area_fp_crown"].sum()]
ax_stack.bar(forests, stem_tot, color=colors, alpha=0.85,
             edgecolor="black", linewidth=0.8)
ax_stack.bar(forests, crown_tot, bottom=stem_tot, color=colors, alpha=0.45,
             hatch="//", edgecolor="black", linewidth=0.8)
ax_stack.set_ylabel("Total estimated surface area (m²)")
ax_stack.set_title("Total surface area: main stem (solid) + crown (hatched)")
ax_stack.grid(axis="y", alpha=0.3)
for i, (s, c) in enumerate(zip(stem_tot, crown_tot)):
    ax_stack.text(i, s + c + 0.5, f"{s + c:.0f} m²", ha="center",
                  va="bottom", fontsize=10)
plt.tight_layout()

# --- Figure: area-normalized stand metrics (basal area & stem density per ha) ---
area_tf = n_plots_tf * PLOT_AREA_HA
area_ca = n_plots_ca * PLOT_AREA_HA
ba_ha = [df_calc_tf["Basal_area"].sum() / area_tf,
         df_calc_ca["Basal_area"].sum() / area_ca]
dens_ha = [len(df_calc_tf) / area_tf, len(df_calc_ca) / area_ca]

fig, (ax_ba, ax_den) = plt.subplots(1, 2, figsize=(12, 6))

bars = ax_ba.bar(forests, ba_ha, color=colors, alpha=0.85,
                 edgecolor="black", linewidth=0.8)
ax_ba.set_ylabel("Basal area (m²/ha)")
ax_ba.set_title(f"Stand basal area  (per-plot = {PLOT_SIZE_M2:.0f} m²)")
ax_ba.grid(axis="y", alpha=0.3)
for bar, v in zip(bars, ba_ha):
    ax_ba.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.0f}",
               ha="center", va="bottom", fontsize=10)

bars = ax_den.bar(forests, dens_ha, color=colors, alpha=0.85,
                  edgecolor="black", linewidth=0.8)
ax_den.set_ylabel("Stem density (trees/ha)")
ax_den.set_title("Stem density")
ax_den.grid(axis="y", alpha=0.3)
for bar, v in zip(bars, dens_ha):
    ax_den.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.0f}",
                ha="center", va="bottom", fontsize=10)
plt.tight_layout()

# --- Figure: per-plot spread (each point = one plot; bar = mean ± SD of plots) ---
rng = np.random.default_rng(0)


def plot_by_plot(ax, column, ylabel, title):
    for i, (per_plot, c) in enumerate(zip([per_plot_tf, per_plot_ca], colors)):
        vals = per_plot[column]
        jitter = rng.normal(i, 0.04, len(vals))
        ax.scatter(jitter, vals, color=c, s=70, alpha=0.85,
                   edgecolor="black", linewidth=0.6, zorder=3)
        ax.errorbar(i, vals.mean(), yerr=vals.std(), fmt="_", color="black",
                    capsize=10, lw=2, markersize=40, zorder=2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(forests)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)


fig, (ax_ph, ax_pb) = plt.subplots(1, 2, figsize=(12, 6))
plot_by_plot(ax_ph, "Height_mean_m", "Plot-mean height (m)",
             "Per-plot mean height\n(points = plots, bar = mean ± SD across plots)")
plot_by_plot(ax_pb, "Basal_area_m2_per_ha", "Basal area (m²/ha)",
             "Per-plot basal area\n(points = plots, bar = mean ± SD across plots)")
plt.tight_layout()

# ----------------------------------------------------------------------
# Figure: estimation bandwidth (mean +/- SD)
#   (a) DBH per plot  (b) DBH per forest  (c) height per forest  (d) SA per forest
# Per-plot bars use the within-plot SD; per-forest bars use the POOLED
# tree-level SD (spread across all trees) = the bandwidth of the estimates.
# ----------------------------------------------------------------------
from matplotlib.patches import Patch

fig, ((ax_dbh_plot, ax_dbh_for),
      (ax_h_for, ax_sa_for)) = plt.subplots(2, 2, figsize=(14, 10))

# (a) per-plot mean DBH +/- within-plot SD (each bar = one plot)
plot_codes = list(per_plot_tf.index) + list(per_plot_ca.index)
plot_means = list(per_plot_tf["DBH_mean_cm"]) + list(per_plot_ca["DBH_mean_cm"])
plot_stds = list(per_plot_tf["DBH_std_cm"]) + list(per_plot_ca["DBH_std_cm"])
plot_colors = [colors[0]] * len(per_plot_tf) + [colors[1]] * len(per_plot_ca)
x = np.arange(len(plot_codes))
ax_dbh_plot.bar(x, plot_means, yerr=plot_stds, capsize=4, color=plot_colors,
                alpha=0.85, edgecolor="black", linewidth=0.6,
                error_kw=dict(ecolor="black", lw=1.2))
ax_dbh_plot.set_xticks(x)
ax_dbh_plot.set_xticklabels(plot_codes, rotation=45, ha="right", fontsize=8)
ax_dbh_plot.set_ylabel("DBH (cm)")
ax_dbh_plot.set_title("(a) Per-plot mean DBH ± within-plot SD")
ax_dbh_plot.grid(axis="y", alpha=0.3)
ax_dbh_plot.legend(handles=[Patch(facecolor=colors[0], alpha=0.85,
                                  edgecolor="black", label="Terra Firme"),
                            Patch(facecolor=colors[1], alpha=0.85,
                                  edgecolor="black", label="Campinarana")],
                   fontsize=9)


def forest_bar(ax, tf_vals, ca_vals, tf_plot_means, ca_plot_means,
               ylabel, title, unit):
    """Per-forest mean with TWO error bars:
      wide/light  = SD across all trees (per-tree estimation bandwidth)
      narrow/bold = SD across plot means (between-plot / stand-level spread)."""
    means = [tf_vals.mean(), ca_vals.mean()]
    tree_sd = [tf_vals.std(), ca_vals.std()]
    plot_sd = [tf_plot_means.std(), ca_plot_means.std()]
    xpos = np.arange(len(forests))
    ax.bar(xpos, means, color=colors, alpha=0.85, edgecolor="black", linewidth=0.8)
    ax.errorbar(xpos - 0.08, means, yerr=tree_sd, fmt="none", ecolor="0.35",
                lw=1.5, capsize=11, capthick=1.5, alpha=0.9)
    ax.errorbar(xpos + 0.08, means, yerr=plot_sd, fmt="none", ecolor="black",
                lw=3, capsize=5, capthick=3)
    ax.set_xticks(xpos)
    ax.set_xticklabels(forests)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    for xi, m, ts, ps in zip(xpos, means, tree_sd, plot_sd):
        ax.text(xi, m + ts, f"{m:.1f} {unit}\n±{ts:.1f} tree / ±{ps:.1f} plot",
                ha="center", va="bottom", fontsize=8)


forest_bar(ax_dbh_for, df_calc_tf["DBH"], df_calc_ca["DBH"],
           per_plot_tf["DBH_mean_cm"], per_plot_ca["DBH_mean_cm"],
           "DBH (cm)", "(b) Per-forest mean DBH ± SD (all trees)", "cm")
forest_bar(ax_h_for, h_tf, h_ca,
           per_plot_tf["Height_mean_m"], per_plot_ca["Height_mean_m"],
           "Height (m)", "(c) Per-forest mean height ± SD (all trees)", "m")
forest_bar(ax_sa_for, sa_tf, sa_ca,
           per_plot_tf["SA_per_tree_mean_m2"], per_plot_ca["SA_per_tree_mean_m2"],
           "Surface area per tree (m²)",
           "(d) Per-forest mean surface area ± SD (all trees)", "m²")

# One shared legend explaining the two error-bar styles
ax_dbh_for.legend(handles=[
    Line2D([0], [0], color="0.35", lw=1.5, label="SD across trees (per-tree spread)"),
    Line2D([0], [0], color="black", lw=3, label="SD across plots (between-plot spread)"),
], fontsize=8, loc="upper right")
plt.tight_layout()

plt.show()