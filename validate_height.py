"""
Height-model validation against real measured tree heights (ATTO context).

Compares candidate DBH -> height models to the Chave (2014) direct-harvest
dataset (real measured DBH + height), focused on Amazonian sites near ATTO:

  Feldpausch (2011) region x precip-class coefficients  (feldpausch_coefficients.csv)
  Chave (2014) E-based pantropical height  (E sampled from E.nc at ATTO plots)

Key questions:
  - Which regional coefficient set best matches real central/N-Amazon heights?
  - How far off are the pipeline's current choices (Guyana-Moist for TF,
    Guyana-Dry for Caa)?  NB: Dry/Moist/Wet are RAINFALL classes, not forest
    types, so this quantifies the cost of that mapping.

Reference sites (measured heights, span small -> large trees):
  BraMan2   = Manaus terra firme (closest analog to ATTO, DBH <= 38 cm)
  FrenchGu  = French Guiana (Guyana Shield terra firme, big trees to ~48 m)
  Venezuela2= N-Amazon (upper Rio Negro)
Caveat: the harvest data partly underlies Feldpausch/Chave, so this is a
consistency check, not a fully independent test. Still the best real-world
height data on hand.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent
HARVEST = BASE / "Tree_data/ATTO/pantropical_allometry/pantropical_allometry/Chave_GCB_Direct_Harvest_Data.csv"
COEF = BASE / "feldpausch_coefficients.csv"
OUT = BASE / "figures_area_estimation"
OUT.mkdir(exist_ok=True)

E_ATTO = -0.1086   # mean of E.nc sampled at the 15 ATTO plots (TF ~ -0.104, Caa ~ -0.115)

# ---------------------------------------------------------------- load data
h = pd.read_csv(HARVEST, sep=None, engine="python")
h.columns = ["Site", "DBH", "H", "AGB", "WSG"]
cf = pd.read_csv(COEF)

CORE = ["BraMan2", "FrenchGu", "Venezuela2"]   # scatter + pooled metrics
AMZ = ("Bra", "Col", "Peru", "FrenchGu", "Venez")   # broader per-site context
core = h[h.Site.isin(CORE)].copy()

# ---------------------------------------------------------------- models
def feld(region, cls):
    r = cf[(cf.region == region) & (cf.precip_class == cls)].iloc[0]
    return lambda d: np.exp(r.beta0 + r.beta1 * np.log(d) + r.sigma)

def chave(d, E=E_ATTO):
    return np.exp(0.893 - E + 0.760 * np.log(d) - 0.0340 * np.log(d) ** 2)

MODELS = {
    "Feld Guyana-Moist  (curr. TF)": feld("Guyana Shield", "Moist"),
    "Feld Guyana-Dry    (curr. Caa)": feld("Guyana Shield", "Dry"),
    "Feld EastCentral-Moist": feld("East-Central Amazonia", "Moist"),
    "Feld Brazilian-Moist": feld("Brazilian Shield", "Moist"),
    "Chave-2014 E (ATTO)": chave,
}

# ---------------------------------------------------------------- metrics
def metrics(pred, obs):
    pred, obs = np.asarray(pred, float), np.asarray(obs, float)
    e = pred - obs
    return pd.Series({
        "bias_m": e.mean(),
        "MAE_m": np.abs(e).mean(),
        "RMSE_m": np.sqrt((e ** 2).mean()),
        "bias_%": 100 * (e / obs).mean(),
    })

print(f"Core reference sites {CORE}: n={len(core)} "
      f"(DBH {core.DBH.min():.0f}-{core.DBH.max():.0f} cm, "
      f"H {core.H.min():.0f}-{core.H.max():.0f} m)\n")

res = pd.DataFrame({name: metrics(f(core.DBH.values), core.H.values)
                    for name, f in MODELS.items()}).T
print("=== Pooled fit on core reference sites (pred - measured) ===")
print(res.round(2).to_string())

# per-site bias (mean pred-obs) across all Amazon sites, for context
amz = h[h.Site.str.startswith(AMZ)].copy()
print("\n=== Per-site mean bias (m), pred - measured ===")
bias_tbl = pd.DataFrame({
    name: amz.groupby("Site").apply(
        lambda g: (f(g.DBH.values) - g.H.values).mean())
    for name, f in MODELS.items()})
bias_tbl.insert(0, "n", amz.groupby("Site").size())
bias_tbl.insert(1, "DBHmax", amz.groupby("Site").DBH.max())
print(bias_tbl.round(1).to_string())

# local reference fit on core sites: ln H = a + b ln D
b, a = np.polyfit(np.log(core.DBH), np.log(core.H), 1)
print(f"\nLocal H-D fit on core sites:  H = exp({a:.3f} + {b:.3f} ln DBH)")

# ---------------------------------------------------------------- figure
palette = {"BraMan2": "#4269d0", "FrenchGu": "#e17c05", "Venezuela2": "#2ca02c"}
mcolors = ["#111111", "#888888", "#d62728", "#9467bd", "#1f77b4"]
dd = np.linspace(5, core.DBH.max(), 200)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6),
                               gridspec_kw={"width_ratios": [1.6, 1]})

for site, g in core.groupby("Site"):
    ax1.scatter(g.DBH, g.H, s=14, alpha=0.45, color=palette[site], label=f"{site} (n={len(g)})")
for (name, f), c in zip(MODELS.items(), mcolors):
    ls = "-" if "curr." in name else "--"
    ax1.plot(dd, f(dd), color=c, lw=2.4, ls=ls, label=name)
ax1.plot(dd, np.exp(a + b * np.log(dd)), color="0.4", lw=1.6, ls=":", label="local fit (core)")
ax1.set_xlabel("DBH (cm)")
ax1.set_ylabel("Tree height (m)")
ax1.set_title("Measured heights vs candidate models\n(central & Guyana-Shield Amazon)")
ax1.grid(alpha=0.3)
ax1.legend(fontsize=8, loc="lower right", framealpha=0.9)

order = res["RMSE_m"].sort_values()
ax2.barh(range(len(order)), order.values, color="#4269d0", alpha=0.85, edgecolor="black")
ax2.set_yticks(range(len(order)))
ax2.set_yticklabels(order.index, fontsize=8)
ax2.invert_yaxis()
ax2.set_xlabel("RMSE (m) on core sites")
ax2.set_title("Height error by model\n(lower = closer to real data)")
ax2.grid(axis="x", alpha=0.3)
for i, v in enumerate(order.values):
    ax2.text(v, i, f" {v:.1f}", va="center", fontsize=8)

fig.tight_layout()
fig.savefig(OUT / "fig_height_validation.png", dpi=150)
print(f"\nSaved figure -> {(OUT / 'fig_height_validation.png')}")
