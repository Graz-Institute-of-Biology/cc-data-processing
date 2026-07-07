import os
import cv2
from gg_image_processing import apply_clahe, detect_dish

src_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\gg_climate_chamber_imgs\\55 zoom"
out_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\gg_climate_chamber_imgs\\failed_detection_retry"
failed_ids = ["5114", "5126", "5144", "5150", "5158", "5165", "5181", "5197"]

os.makedirs(out_dir, exist_ok=True)

for fn in os.listdir(src_dir):
    if not any(fid in fn for fid in failed_ids):
        continue
    if not fn.lower().endswith(".jpg"):
        continue
    name, ext = os.path.splitext(fn)
    bgr = cv2.imread(os.path.join(src_dir, fn))
    clahe_bgr = apply_clahe(bgr)
    mask_path = os.path.join(out_dir, f"{name}_mask{ext}")
    det = detect_dish(clahe_bgr, debug_mask_path=mask_path)
    annotated = clahe_bgr.copy()
    if det is not None:
        cx, cy, r, method = det
        cv2.circle(annotated, (int(cx), int(cy)), int(r), (0, 255, 0), 8)
        cv2.circle(annotated, (int(cx), int(cy)), 6, (0, 0, 255), -1)
        print(f"{fn}: {method} center=({int(cx)},{int(cy)}) r={int(r)}")
    else:
        print(f"{fn}: NO CIRCLE")
    cv2.imwrite(os.path.join(out_dir, f"{name}_circle{ext}"), annotated)
