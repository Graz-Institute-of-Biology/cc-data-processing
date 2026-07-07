import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm


def load_ontology(ontology_path):
    with open(ontology_path, "r") as f:
        data = json.load(f)
    ontology = data["ontology"]

    max_value = max(entry["value"] for entry in ontology.values())
    colors = [(0, 0, 0)] * (max_value + 1)
    labels = [None] * (max_value + 1)
    for name, entry in ontology.items():
        colors[entry["value"]] = hex_to_rgb(entry["color"])
        labels[entry["value"]] = name
    return labels, colors


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def colorize_mask(mask, colors):
    palette = np.zeros((256, 3), dtype=np.uint8)
    for i, c in enumerate(colors):
        palette[i] = c
    return palette[mask]


def draw_legend(img, present_indices, labels, colors, scale=0.022):
    ref = min(img.width, img.height)
    font_size = max(12, int(ref * scale))
    swatch = max(14, int(font_size * 1.2))
    padding = max(6, int(font_size * 0.6))
    gap = max(4, int(font_size * 0.4))
    margin = max(10, int(ref * 0.015))
    outline_w = max(1, int(ref * 0.0015))

    draw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    entries = [(i, labels[i], colors[i]) for i in present_indices if labels[i] is not None]
    if not entries:
        return

    text_widths = [draw.textbbox((0, 0), name, font=font)[2] for _, name, _ in entries]
    line_height = max(swatch, font_size + 4)
    box_w = padding * 2 + swatch + gap + max(text_widths)
    box_h = padding * 2 + line_height * len(entries)

    x0 = img.width - margin - box_w
    y0 = margin
    draw.rectangle([x0, y0, x0 + box_w, y0 + box_h],
                   fill=(255, 255, 255, 220), outline=(0, 0, 0, 255), width=outline_w)

    for idx, (_, name, color) in enumerate(entries):
        ly = y0 + padding + idx * line_height
        sx = x0 + padding
        draw.rectangle([sx, ly, sx + swatch, ly + swatch],
                       fill=color, outline=(0, 0, 0, 255))
        text_y = ly + (swatch - font_size) // 2 - 2
        draw.text((sx + swatch + gap, text_y), name, fill=(0, 0, 0, 255), font=font)


def plot_with_legend(mask_path, save_path, labels, colors):
    mask = np.array(Image.open(mask_path))
    rgb = colorize_mask(mask, colors)
    img = Image.fromarray(rgb, mode="RGB")

    present = np.unique(mask).tolist()
    draw_legend(img, present, labels, colors)

    img.save(save_path)


if __name__ == "__main__":
    ontology_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\ontology_gg.json"
    input_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\02-cc-gg\test_gg_climatechamber_135"
    output_path = input_path

    labels, colors = load_ontology(ontology_path)

    mask_files = [f for f in os.listdir(input_path) if f.endswith("mask.png")]

    for mask_file in tqdm(mask_files):
        mask_path = os.path.join(input_path, mask_file)
        save_path = os.path.join(output_path, mask_file.replace(".png", "_legend.png"))
        plot_with_legend(mask_path, save_path, labels, colors)
