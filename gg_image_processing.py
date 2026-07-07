import os
import json
import cv2
import numpy as np
from PIL import Image, ImageEnhance

img_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\gg_climate_chamber_imgs\\exp_set_oct25"
ref_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\gg_climate_chamber_imgs\\light_references"

brightness_factor = 1.7
clahe_clip_limit = 3.0
clahe_tile_grid = (8, 8)
mask_inset = 0.65
extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")

# Petri dish radius in full-image pixels. The camera-to-dish distance is
# fixed at 90 cm and the dishes are 94 mm in diameter, so the projected
# radius is constant. Calibrated from well-fitted images (5114, 5154).

if img_path.endswith("55 zoom"):
    fixed_dish_radius_px = 565
    detect_width = 1200
    h_denom = 7.0
    # (x_lo, x_hi, y_lo, y_hi) as fractions of detect-image size.
    # 55 zoom: dish is small and central, lots of distractors (rim arc, label).
    roi_bounds = (0.25, 0.75, 0.40, 0.80)

else:
    fixed_dish_radius_px = 1250
    detect_width = 2000
    h_denom = 3.5
    # 135 zoom: dish fills most of the frame, can sit anywhere from
    # center-left to far right and reach close to top/bottom edges.
    roi_bounds = (0.10, 0.98, 0.20, 0.98)


def compute_reference_lab_stats(ref_directory, cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cached = json.load(f)
        return np.array(cached["mean"], dtype=np.float64), np.array(cached["std"], dtype=np.float64)

    sums = np.zeros(3, dtype=np.float64)
    sqsums = np.zeros(3, dtype=np.float64)
    total = 0
    for fn in os.listdir(ref_directory):
        if not fn.lower().endswith(extensions):
            continue
        ref_bgr = cv2.imread(os.path.join(ref_directory, fn))
        if ref_bgr is None:
            continue
        lab_ref = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2LAB).astype(np.float64).reshape(-1, 3)
        sums += lab_ref.sum(axis=0)
        sqsums += (lab_ref ** 2).sum(axis=0)
        total += lab_ref.shape[0]
    if total == 0:
        raise RuntimeError(f"No reference images found in {ref_directory}")
    mean = sums / total
    var = np.maximum(sqsums / total - mean ** 2, 1e-8)
    std = np.sqrt(var)
    with open(cache_file, "w") as f:
        json.dump({"mean": mean.tolist(), "std": std.tolist(), "n_pixels": int(total)}, f)
    return mean, std


def apply_clahe(bgr, clip_limit=clahe_clip_limit, tile_grid=clahe_tile_grid):
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_eq = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l_eq, a, b)), cv2.COLOR_LAB2BGR)


def refine_center_by_rim(gray, cx0, cy0, r, search_r=30, n_samples=120, band=8):
    """Snap (cx0, cy0) to the position where a circle of radius r best
    sits on the dish rim: bright table just outside, darker content just
    inside. Robust to crescent / partial-content masks because it only
    uses the dish boundary, not its interior.
    """
    h, w = gray.shape
    theta = np.linspace(0, 2 * np.pi, n_samples, endpoint=False)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    inner_r = r - band
    outer_r = r + band
    best_cx, best_cy, best_score = cx0, cy0, -1e18
    for dy in range(-search_r, search_r + 1, 2):
        for dx in range(-search_r, search_r + 1, 2):
            cx = cx0 + dx
            cy = cy0 + dy
            xs_in = (cx + inner_r * cos_t).astype(int)
            ys_in = (cy + inner_r * sin_t).astype(int)
            xs_out = (cx + outer_r * cos_t).astype(int)
            ys_out = (cy + outer_r * sin_t).astype(int)
            valid = ((xs_in >= 0) & (xs_in < w) & (ys_in >= 0) & (ys_in < h)
                     & (xs_out >= 0) & (xs_out < w) & (ys_out >= 0) & (ys_out < h))
            if valid.sum() < n_samples * 0.6:
                continue
            inner = gray[ys_in[valid], xs_in[valid]].astype(np.int32)
            outer = gray[ys_out[valid], xs_out[valid]].astype(np.int32)
            score = float((outer - inner).mean())
            if score > best_score:
                best_score = score
                best_cx, best_cy = float(cx), float(cy)
    return best_cx, best_cy


def detect_dish(bgr, debug_mask_path=None):
    """Detect petri dish in `bgr`. Returns (cx, cy, r, method) in full-image
    coordinates, or None if nothing was found.
    """
    h0, w0 = bgr.shape[:2]
    scale = detect_width / w0
    small = cv2.resize(bgr, (detect_width, int(h0 * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Use the fixed (camera-calibrated) radius rather than guessing from
    # h_denom — we know the dish size exactly. Tightening this window
    # rejects label blobs (too small) and merged-with-surroundings blobs
    # (too big) at the contour stage.
    r_fixed_detect = fixed_dish_radius_px * scale
    expected_r = r_fixed_detect
    min_r = r_fixed_detect * 0.80
    max_r = r_fixed_detect * 1.20

    # Morphology kernel sizes. The neck-break opening would over-erode
    # the wavy dish boundary at large zoom levels, so keep it modest.
    close_size = 15
    open_size = 21
    neck_size = 45

    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_size, close_size))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, open_kernel)

    roi_x0 = int(w * roi_bounds[0])
    roi_x1 = int(w * roi_bounds[1])
    roi_y0 = int(h * roi_bounds[2])
    roi_y1 = int(h * roi_bounds[3])
    roi_mask = np.zeros_like(binary)
    roi_mask[roi_y0:roi_y1, roi_x0:roi_x1] = 255
    binary = cv2.bitwise_and(binary, roi_mask)

    # Fill holes inside foreground blobs. Bright lichens fall above Otsu's
    # threshold and would otherwise carve a hole out of the dish blob,
    # pulling the moments centroid / DT peak off-center.
    inv = cv2.bitwise_not(binary)
    n_inv, inv_lbls = cv2.connectedComponents(inv)
    bg_labels = set(np.unique(inv_lbls[0, :]).tolist()) \
        | set(np.unique(inv_lbls[-1, :]).tolist()) \
        | set(np.unique(inv_lbls[:, 0]).tolist()) \
        | set(np.unique(inv_lbls[:, -1]).tolist())
    if n_inv > 1:
        hole_mask = np.isin(inv_lbls, list(bg_labels), invert=True)
        binary[hole_mask] = 255

    # Drop components whose bbox spans most of the ROI width (light stand,
    # rim arc). The dish, even when fused via a thin neck to the stand or
    # rim, has a tight bbox; the stand/rim arcs span the full ROI.
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    roi_w = roi_x1 - roi_x0
    span_limit = int(roi_w * 0.85)
    drop = np.zeros(n_labels, dtype=bool)
    for lbl in range(1, n_labels):
        bbox_w = stats[lbl, cv2.CC_STAT_WIDTH]
        if bbox_w >= span_limit:
            drop[lbl] = True
    if drop.any():
        binary = np.where(drop[labels], 0, binary).astype(np.uint8)

    # Break thicker necks between dish and surrounding dark structures.
    neck_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (neck_size, neck_size))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, neck_kernel)

    if debug_mask_path is not None:
        cv2.imwrite(debug_mask_path, binary)

    max_area = np.pi * max_r * max_r * 1.2

    blob_result = None
    method = None

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for cnt in contours:
        (bx, by), br = cv2.minEnclosingCircle(cnt)
        if not (min_r <= br <= max_r):
            continue
        area = cv2.contourArea(cnt)
        if area > max_area:
            continue
        fill_ratio = area / (3.14159 * br * br)
        if fill_ratio < 0.5:
            continue
        perim = cv2.arcLength(cnt, True)
        circularity = (4 * 3.14159 * area) / (perim * perim) if perim > 0 else 0
        if circularity < 0.6:
            continue
        # Use moments centroid + area-derived radius — robust to a small
        # neck where the dish blob merges with the light stand above.
        M = cv2.moments(cnt)
        if M["m00"] <= 0:
            continue
        cx_m = M["m10"] / M["m00"]
        cy_m = M["m01"] / M["m00"]
        r_area = np.sqrt(area / np.pi)
        # Score: closeness of enclosing-circle radius to the known dish
        # radius. Tiebreaker by circularity. This avoids picking a small
        # label blob over the dish when both pass the loose radius window.
        r_err = abs(br - r_fixed_detect) / r_fixed_detect
        candidates.append((cx_m, cy_m, r_area, r_err, circularity))
    if candidates:
        bx, by, br, _, _ = min(candidates, key=lambda c: (c[3], -c[4]))
        blob_result = (bx, by, br)
        method = "blob"

    if blob_result is None:
        # Relaxed pass for crescent / partial blobs (e.g. when bright
        # lichens carve open one side of the dish). The bounding box of
        # such a blob still spans the dish — its center is a reliable
        # estimate even when circularity / fill-ratio fail.
        relaxed = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 2 * min_r * 0.8 and bh < 2 * min_r * 0.8:
                continue
            if bw > 2 * max_r * 1.1 or bh > 2 * max_r * 1.1:
                continue
            area = cv2.contourArea(cnt)
            if area < np.pi * min_r * min_r * 0.25:
                continue
            relaxed.append((x + bw / 2.0, y + bh / 2.0, area))
        if relaxed:
            cx_r, cy_r, _ = max(relaxed, key=lambda c: c[2])
            blob_result = (cx_r, cy_r, expected_r)
            method = "bbox"

    if blob_result is None:
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        peak_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
        dilated = cv2.dilate(dist, peak_kernel)
        is_peak = (dist == dilated) & (dist >= min_r) & (dist <= max_r)
        ys, xs = np.where(is_peak)
        dt_candidates = []
        for cy_p, cx_p in zip(ys, xs):
            r_p = float(dist[cy_p, cx_p])
            test_mask = np.zeros_like(binary)
            cv2.circle(test_mask, (int(cx_p), int(cy_p)), int(r_p), 255, -1)
            inside = test_mask > 0
            if inside.sum() == 0:
                continue
            coverage = float((binary[inside] > 0).sum()) / float(inside.sum())
            if coverage < 0.85:
                continue
            dt_candidates.append((float(cx_p), float(cy_p), r_p, coverage))
        if dt_candidates:
            cx_d, cy_d, r_d, _ = max(dt_candidates, key=lambda c: c[1])
            blob_result = (cx_d, cy_d, r_d)
            method = "dt"

    if blob_result is None:
        # The dish has a transparent plastic rim that creates a faint
        # circular outline regardless of contents (works even when bright
        # lichens make the dish blob unusable). Hough constrained to the
        # known radius is strong enough to find it.
        gray_blur = cv2.medianBlur(gray, 5)
        roi_only = np.zeros_like(gray_blur)
        roi_only[roi_y0:roi_y1, roi_x0:roi_x1] = gray_blur[roi_y0:roi_y1, roi_x0:roi_x1]
        circles = cv2.HoughCircles(
            roi_only,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=int(r_fixed_detect),
            param1=120,
            param2=25,
            minRadius=int(r_fixed_detect * 0.92),
            maxRadius=int(r_fixed_detect * 1.08),
        )
        if circles is not None:
            cx_h, cy_h, r_h = max(circles[0], key=lambda c: c[2])
            blob_result = (cx_h, cy_h, r_h)
            method = "hough"

    if blob_result is None:
        return None

    cx0, cy0, _ = blob_result

    # Snap center to the deepest interior point near the moments centroid.
    # The dish region has the largest distance-to-background (~dish radius);
    # a thin neck where the dish merges with the stand has a much smaller
    # value, so this corrects the upward bias from the neck.
    # Skip for bbox/hough methods — they already give a geometry-based
    # center that we don't want to pull back into the partial blob mass.
    if method == "blob":
        dt = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        search_r = int(expected_r * 0.6)
        sy0 = max(0, int(cy0) - search_r)
        sy1 = min(h, int(cy0) + search_r + 1)
        sx0 = max(0, int(cx0) - search_r)
        sx1 = min(w, int(cx0) + search_r + 1)
        window = dt[sy0:sy1, sx0:sx1]
        if window.size > 0 and window.max() > 0:
            local = np.unravel_index(int(window.argmax()), window.shape)
            cx0 = float(sx0 + local[1])
            cy0 = float(sy0 + local[0])

    # Rim refinement: snap the center to the position where the dish's
    # bright-table / dark-content boundary best aligns with a circle of
    # the known radius. Works regardless of what's inside the dish.
    rim_band = max(6, int(round(r_fixed_detect * 0.07)))
    rim_search = max(30, int(round(r_fixed_detect * 0.08)))
    cx0, cy0 = refine_center_by_rim(
        gray, cx0, cy0, r_fixed_detect,
        search_r=rim_search, band=rim_band,
    )

    cx = cx0 / scale
    cy = cy0 / scale
    return (cx, cy, float(fixed_dish_radius_px), method)


def reinhard_match(bgr, region_mask, ref_mean, ref_std):
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float64)
    pixels = lab[region_mask > 0]
    if pixels.shape[0] == 0:
        return bgr.copy()
    in_mean = pixels.mean(axis=0)
    in_std = np.maximum(pixels.std(axis=0), 1e-8)
    out = (lab - in_mean) / in_std * ref_std + ref_mean
    out = np.clip(out, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_LAB2BGR)


def match_lighting_and_crop(bgr, cx, cy, r, ref_mean, ref_std):
    H, W = bgr.shape[:2]
    stats_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(stats_mask, (int(cx), int(cy)), int(r * mask_inset), 255, -1)
    matched = reinhard_match(bgr, stats_mask, ref_mean, ref_std)

    x0 = int(max(0, cx - r))
    y0 = int(max(0, cy - r))
    x1 = int(min(W, cx + r))
    y1 = int(min(H, cy + r))
    crop = matched[y0:y1, x0:x1].copy()
    crop_mask = np.zeros(crop.shape[:2], dtype=np.uint8)
    cv2.circle(crop_mask, (int(cx - x0), int(cy - y0)), int(r), 255, -1)
    crop[crop_mask == 0] = 0
    return crop


def save_simple_brightened(src_path, out_path):
    with Image.open(src_path) as img:
        ImageEnhance.Brightness(img).enhance(brightness_factor).save(out_path)


def process_image(filename, src_dir, paths, ref_mean, ref_std):
    src = os.path.join(src_dir, filename)
    name, ext = os.path.splitext(filename)

    save_simple_brightened(src, os.path.join(paths["brightened"], f"{name}_b{brightness_factor}{ext}"))

    bgr = cv2.imread(src)
    clahe_bgr = apply_clahe(bgr)
    clahe_name = f"{name}_clahe_c{clahe_clip_limit}_t{clahe_tile_grid[0]}{ext}"
    cv2.imwrite(os.path.join(paths["clahe"], clahe_name), clahe_bgr)

    debug_mask_path = os.path.join(paths["circle"], f"{name}_mask{ext}")
    detection = detect_dish(clahe_bgr, debug_mask_path=debug_mask_path)

    annotated = clahe_bgr.copy()
    if detection is not None:
        cx, cy, r, method = detection
        cv2.circle(annotated, (int(cx), int(cy)), int(r), (0, 255, 0), 8)
        cv2.circle(annotated, (int(cx), int(cy)), 6, (0, 0, 255), -1)
        print(f"  {method}: center=({int(cx)},{int(cy)}) r={int(r)}")
    else:
        print(f"  no circle found")
    cv2.imwrite(os.path.join(paths["circle"], f"{name}_circle{ext}"), annotated)

    if detection is not None:
        cx, cy, r, _ = detection
        crop = match_lighting_and_crop(bgr, cx, cy, r, ref_mean, ref_std)
        cv2.imwrite(os.path.join(paths["dish"], f"{name}_dish{ext}"), crop)

    print(f"Processed {filename}")


def main():
    paths = {
        "brightened": img_path + "_brightened",
        "clahe": img_path + "_clahe",
        "circle": img_path + "_circle",
        "dish": img_path + "_lightmatched",
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)

    ref_mean, ref_std = compute_reference_lab_stats(ref_dir, os.path.join(ref_dir, "_lab_stats.json"))
    print(f"Reference LAB mean={ref_mean.round(2)} std={ref_std.round(2)}")

    for filename in os.listdir(img_path):
        if not filename.lower().endswith(extensions):
            continue
        process_image(filename, img_path, paths, ref_mean, ref_std)


if __name__ == "__main__":
    main()
