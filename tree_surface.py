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
df_calc_tf["Estimated_surface_area_fp"] = df_calc_tf["Estimated_height_feldpausch"] * np.pi * (df_calc_tf["Radius_bottom"]/100 + df_calc_tf["Radius_top"]/100)
print(df_calc_tf.sort_values("DBH"))


print("Campinarana Trees:")
print(ca_trees[["NO", "DBH"]])
df_calc_ca["NO"] = ca_trees["NO"]
df_calc_ca["DBH"] = ca_trees["DBH"]
df_calc_ca["Radius_bottom"] = df_calc_ca["DBH"] * 0.5
df_calc_ca["Radius_top"] = df_calc_ca["Radius_bottom"] *0.7
# df_calc_ca["Estimated_height_chaves"] = np.exp(0.893 - E_ca + 0.760*np.log(ca_trees["DBH"]) - 0.0340*(np.log(ca_trees["DBH"])**2)) # ln(H) = 0.893 - E +0.760*ln(D) - 0.0340*|ln(D)|²
df_calc_ca["Estimated_height_feldpausch"] = np.exp(beta_zero_moist_ca + beta_one_moist_ca * np.log(ca_trees["DBH"]) + kappa_moist_ca) # log(H ) = beta_zero_moist + beta_one_moist log(DBH) + kappa_moist
# df_calc_ca["Estimated_surface_area_ch"] = df_calc_ca["Estimated_height_chaves"] * np.pi * (df_calc_ca["Radius_bottom"]/100 + df_calc_ca["Radius_top"]/100)
df_calc_ca["Estimated_surface_area_fp"] = df_calc_ca["Estimated_height_feldpausch"] * np.pi * (df_calc_ca["Radius_bottom"]/100 + df_calc_ca["Radius_top"]/100)
print(df_calc_ca.sort_values("DBH"))


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
plt.show()