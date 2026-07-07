"""Compare entropy distributions between two result folders (55mm vs 135mm).

Each folder contains pairs of <name>_dish_entropy.png (viridis-colormapped)
and <name>_dish_mask.png (class indices). Original dish JPGs in the sibling
compare_<setup> folders are used to detect the petri-dish ROI so the
comparison is restricted to inside-dish pixels.
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm
from PIL import Image
from scipy.spatial import cKDTree
from tqdm import tqdm

RESULTS_ROOT = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\02-cc-gg"
ONTOLOGY_PATH = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\ontology_gg.json"
OUT_DIR = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\02-cc-gg\entropy_comparison"

SETUPS = {
    "55mm":  ("test_gg_climatechamber_55",  "compare_55"),
    "135mm": ("test_gg_climatechamber_135", "compare_135"),
}

# entropy values reported are in [0, 1] (recovered from the 8-bit viridis PNG)
HIGH_ENTROPY_THRESHOLD = 0.5


def build_viridis_inverse_lut(n=512):
    """KDTree over the viridis colormap so we can map RGB → scalar in [0, 1]."""
    samples = np.linspace(0.0, 1.0, n)
    rgb = (cm.get_cmap("viridis")(samples)[:, :3] * 255).astype(np.uint8)
    return cKDTree(rgb.astype(np.float32)), samples


def recover_entropy(entropy_png_path, kdtree, samples):
    rgba = np.array(Image.open(entropy_png_path))
    rgb = rgba[..., :3].reshape(-1, 3).astype(np.float32)
    _, idx = kdtree.query(rgb, k=1)
    return samples[idx].reshape(rgba.shape[:2]).astype(np.float32)


def detect_dish_roi(jpg_path, fallback_radius_frac=0.48):
    img = cv2.imread(jpg_path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    blurred = cv2.GaussianBlur(img, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2,
        minDist=max(h, w),
        param1=120, param2=40,
        minRadius=int(min(h, w) * 0.35),
        maxRadius=int(min(h, w) * 0.55),
    )
    if circles is not None:
        cx, cy, r = circles[0, 0]
    else:
        cx, cy, r = w / 2, h / 2, min(h, w) * fallback_radius_frac

    # shrink slightly so the rim (often misclassified) is excluded
    r = r * 0.97
    yy, xx = np.ogrid[:h, :w]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2


def load_labels(ontology_path):
    with open(ontology_path) as f:
        ontology = json.load(f)["ontology"]
    max_val = max(e["value"] for e in ontology.values())
    labels = [None] * (max_val + 1)
    for name, e in ontology.items():
        labels[e["value"]] = name
    return labels


def collect_stats(entropy_folder, jpg_folder, labels, kdtree, samples):
    rows = []
    all_entropy = []
    mask_files = sorted(f for f in os.listdir(entropy_folder) if f.endswith("_mask.png"))

    for mask_file in tqdm(mask_files, desc=os.path.basename(entropy_folder)):
        stem = mask_file.replace("_mask.png", "")
        entropy_file = os.path.join(entropy_folder, f"{stem}_entropy.png")
        jpg_file = os.path.join(jpg_folder, f"{stem}.JPG")
        if not (os.path.exists(entropy_file) and os.path.exists(jpg_file)):
            continue

        entropy = recover_entropy(entropy_file, kdtree, samples)
        mask = np.array(Image.open(os.path.join(entropy_folder, mask_file)))
        roi = detect_dish_roi(jpg_file)

        vals = entropy[roi]
        row = {
            "image": stem,
            "n_pixels_in_roi": int(roi.sum()),
            "mean_entropy": float(vals.mean()),
            "median_entropy": float(np.median(vals)),
            "p90_entropy": float(np.percentile(vals, 90)),
            "high_entropy_frac": float((vals > HIGH_ENTROPY_THRESHOLD).mean()),
        }
        for cls_idx, cls_name in enumerate(labels):
            if cls_name is None:
                continue
            cls_mask = roi & (mask == cls_idx)
            if cls_mask.sum() == 0:
                row[f"mean_entropy__{cls_name}"] = np.nan
                row[f"pixel_frac__{cls_name}"] = 0.0
            else:
                row[f"mean_entropy__{cls_name}"] = float(entropy[cls_mask].mean())
                row[f"pixel_frac__{cls_name}"] = float(cls_mask.sum() / roi.sum())
        rows.append(row)
        all_entropy.append(vals)

    df = pd.DataFrame(rows)
    pooled = np.concatenate(all_entropy) if all_entropy else np.array([])
    return df, pooled


def plot_comparison(per_setup_df, per_setup_pooled, labels, out_dir):
    setups = list(per_setup_df)
    colors = {"55mm": "#1f77b4", "135mm": "#d62728"}

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # 1. pooled entropy histogram
    ax = axes[0, 0]
    bins = np.linspace(0, 1, 60)
    for s in setups:
        ax.hist(per_setup_pooled[s], bins=bins, alpha=0.5,
                label=f"{s}  (n={len(per_setup_pooled[s]):,} px)",
                color=colors[s], density=True)
    ax.axvline(HIGH_ENTROPY_THRESHOLD, ls="--", c="k", lw=1, label=f"high-entropy threshold = {HIGH_ENTROPY_THRESHOLD}")
    ax.set_xlabel("entropy (normalised, 0..1)")
    ax.set_ylabel("density")
    ax.set_title("Pooled pixel-level entropy inside dish ROI")
    ax.legend()

    # 2. per-image mean entropy boxplot
    ax = axes[0, 1]
    data = [per_setup_df[s]["mean_entropy"].values for s in setups]
    bp = ax.boxplot(data, labels=setups, patch_artist=True, showmeans=True)
    for patch, s in zip(bp["boxes"], setups):
        patch.set_facecolor(colors[s])
        patch.set_alpha(0.5)
    ax.set_ylabel("mean entropy per image")
    ax.set_title("Per-image mean entropy")

    # 3. per-image high-entropy fraction boxplot
    ax = axes[1, 0]
    data = [per_setup_df[s]["high_entropy_frac"].values for s in setups]
    bp = ax.boxplot(data, labels=setups, patch_artist=True, showmeans=True)
    for patch, s in zip(bp["boxes"], setups):
        patch.set_facecolor(colors[s])
        patch.set_alpha(0.5)
    ax.set_ylabel(f"fraction of pixels with entropy > {HIGH_ENTROPY_THRESHOLD}")
    ax.set_title("High-entropy pixel fraction per image")

    # 4. per-class mean entropy (bar chart)
    ax = axes[1, 1]
    class_names = [l for l in labels if l is not None]
    x = np.arange(len(class_names))
    width = 0.4
    for i, s in enumerate(setups):
        means = [per_setup_df[s][f"mean_entropy__{c}"].mean() for c in class_names]
        ax.bar(x + (i - 0.5) * width, means, width, label=s,
               color=colors[s], alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, rotation=30, ha="right")
    ax.set_ylabel("mean entropy (over images, of pixels predicted as that class)")
    ax.set_title("Per-class mean entropy")
    ax.legend()

    fig.tight_layout()
    out_path = os.path.join(out_dir, "entropy_comparison.png")
    fig.savefig(out_path, dpi=150)
    print(f"figure -> {out_path}")


def print_summary(per_setup_df, per_setup_pooled, labels):
    print("\n=== Summary (entropy normalised to 0..1) ===")
    rows = []
    for s, df in per_setup_df.items():
        pooled = per_setup_pooled[s]
        rows.append({
            "setup": s,
            "n_images": len(df),
            "pooled_mean": pooled.mean(),
            "pooled_median": float(np.median(pooled)),
            "img_mean_entropy_mean": df["mean_entropy"].mean(),
            "img_mean_entropy_std":  df["mean_entropy"].std(),
            "img_high_entropy_frac_mean": df["high_entropy_frac"].mean(),
        })
    summary = pd.DataFrame(rows).set_index("setup")
    with pd.option_context("display.float_format", "{:.4f}".format,
                           "display.width", 140):
        print(summary)

    print("\n=== Per-class mean entropy (averaged across images) ===")
    class_names = [l for l in labels if l is not None]
    cls_rows = {}
    for s, df in per_setup_df.items():
        cls_rows[s] = {c: df[f"mean_entropy__{c}"].mean() for c in class_names}
    with pd.option_context("display.float_format", "{:.4f}".format):
        print(pd.DataFrame(cls_rows))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    labels = load_labels(ONTOLOGY_PATH)
    kdtree, samples = build_viridis_inverse_lut()

    per_setup_df = {}
    per_setup_pooled = {}
    for setup, (entropy_sub, jpg_sub) in SETUPS.items():
        entropy_folder = os.path.join(RESULTS_ROOT, entropy_sub)
        jpg_folder = os.path.join(RESULTS_ROOT, jpg_sub)
        df, pooled = collect_stats(entropy_folder, jpg_folder, labels, kdtree, samples)
        df.to_csv(os.path.join(OUT_DIR, f"entropy_stats_{setup}.csv"), index=False)
        per_setup_df[setup] = df
        per_setup_pooled[setup] = pooled

    print_summary(per_setup_df, per_setup_pooled, labels)
    plot_comparison(per_setup_df, per_setup_pooled, labels, OUT_DIR)


if __name__ == "__main__":
    main()
