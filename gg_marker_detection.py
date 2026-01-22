"""
Marker Detection and Filtering Script

Processes paired images and masks to detect and classify field plot markers:
- Type 1: Silver Herring (metallic gray, larger fragments)
- Type 2: Red Nails (round, red/pink color)

Usage:
    Modify the IMAGE_FOLDER and MASK_FOLDER paths, then run the script.
"""

import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from scipy import ndimage
from colorsys import rgb_to_hsv
import matplotlib.pyplot as plt
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

IMAGE_FOLDER = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\gg_find_markers\test_set\images"  # Folder containing .JPG images
MASK_FOLDER = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\gg_find_markers\test_set\masks"   # Folder containing _mask.png files
OUTPUT_FOLDER = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\gg_find_markers\test_set\results"    # Where to save visualizations

MARKER_CLASS = 8          # Mask value for markers
MIN_SIZE_PIXELS = 500    # Minimum fragment size to consider valid

# Type 2 (Red Nail) shape thresholds
TYPE2_MAX_ECCENTRICITY = 0.50
TYPE2_MIN_CIRCULARITY = 0.5
TYPE2_MIN_FILL_RATIO = 0.6
TYPE2_MIN_SIZE = 500
TYPE2_MAX_SIZE = 6000

# Type 2 (Red Nail) color thresholds
TYPE2_MIN_RED_MEAN = 130
TYPE2_MIN_RED_DOMINANT_PCT = 50

# Type 1 (Silver Herring) shape thresholds
TYPE1_MAX_ASPECT_RATIO = 2.5  # Herrings are not extremely elongated
TYPE1_MIN_SIZE = 5000

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_exif_rotation(image_path):
    """Read EXIF orientation and return the required np.rot90 k value."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if exif_data:
            orientation = exif_data.get(274, 1)  # 274 = Orientation tag
            # Map EXIF orientation to np.rot90 k value
            rotation_map = {
                1: 0,   # Normal - no rotation
                3: 2,   # Rotated 180°
                6: 3,   # Rotated 90° CW -> need rot90 k=3
                8: 1,   # Rotated 90° CCW -> need rot90 k=1
            }
            return rotation_map.get(orientation, 0)
    except Exception as e:
        print(f"  Warning: Could not read EXIF from {image_path}: {e}")
    return 0


def load_and_align_images(image_path, mask_path):
    """Load image and mask, align them using EXIF rotation info."""
    # Load mask (no rotation needed)
    mask = np.array(Image.open(mask_path))
    
    # Load image and check rotation
    rgb_orig = np.array(Image.open(image_path))
    k = get_exif_rotation(image_path)
    
    if k != 0:
        rgb = np.rot90(rgb_orig, k=k)
    else:
        rgb = rgb_orig
    
    # Verify alignment
    if mask.shape[:2] != rgb.shape[:2]:
        raise ValueError(f"Shape mismatch: mask {mask.shape[:2]} vs image {rgb.shape[:2]}")
    
    return rgb, mask, k


def compute_shape_features(obj_mask):
    """Compute shape features for a binary object mask."""
    coords = np.where(obj_mask)
    size = len(coords[0])
    
    if size == 0:
        return None
    
    y_min, y_max = coords[0].min(), coords[0].max()
    x_min, x_max = coords[1].min(), coords[1].max()
    height = y_max - y_min + 1
    width = x_max - x_min + 1
    
    bbox_area = height * width
    fill_ratio = size / bbox_area
    aspect_ratio = width / height
    eccentricity = 1 - (min(height, width) / max(height, width))
    
    # Circularity
    eroded = ndimage.binary_erosion(obj_mask)
    perimeter = np.sum(obj_mask) - np.sum(eroded)
    circularity = (4 * np.pi * size) / (perimeter ** 2) if perimeter > 0 else 0
    
    return {
        'size': size,
        'bbox': (y_min, x_min, height, width),
        'center': (int((y_min + y_max) / 2), int((x_min + x_max) / 2)),
        'aspect_ratio': aspect_ratio,
        'fill_ratio': fill_ratio,
        'circularity': circularity,
        'eccentricity': eccentricity,
    }


def compute_color_features(rgb, obj_mask):
    """Compute color features for pixels within an object mask."""
    coords = np.where(obj_mask)
    
    r_vals = rgb[coords[0], coords[1], 0].astype(float)
    g_vals = rgb[coords[0], coords[1], 1].astype(float)
    b_vals = rgb[coords[0], coords[1], 2].astype(float)
    
    mean_r, mean_g, mean_b = r_vals.mean(), g_vals.mean(), b_vals.mean()
    h, s, v = rgb_to_hsv(mean_r/255, mean_g/255, mean_b/255)
    
    # Red dominant percentage
    red_dominant_pct = 100 * np.sum((r_vals > g_vals) & (r_vals > b_vals)) / len(r_vals)
    
    return {
        'mean_rgb': (mean_r, mean_g, mean_b),
        'hsv': (h * 360, s, v),
        'red_dominant_pct': red_dominant_pct,
    }


def classify_marker(shape_feat, color_feat):
    """
    Classify a marker object as Type 1 (Herring), Type 2 (Red Nail), or None.
    
    Returns: ("Type 1", "Silver Herring") or ("Type 2", "Red Nail") or None
    """
    size = shape_feat['size']
    
    # Size filter first
    if size < MIN_SIZE_PIXELS:
        return None
    
    # print(color_feat)
    # print(shape_feat)
    
    # Type 2: Red Nail (round + red)
    below_max_ecc = shape_feat['eccentricity'] < TYPE2_MAX_ECCENTRICITY
    above_min_circ = shape_feat['circularity'] > TYPE2_MIN_CIRCULARITY
    above_min_fill = shape_feat['fill_ratio'] > TYPE2_MIN_FILL_RATIO
    is_round = (below_max_ecc and
                above_min_circ and
                above_min_fill)

    above_red_mean = color_feat['mean_rgb'][0] > TYPE2_MIN_RED_MEAN
    red_dominant = color_feat['red_dominant_pct'] > TYPE2_MIN_RED_DOMINANT_PCT
    is_red = (above_red_mean and red_dominant)
    
    is_right_size_for_nail = TYPE2_MIN_SIZE < size < TYPE2_MAX_SIZE

    # print("Below max ecc:", below_max_ecc)
    # print("Above min circ:", above_min_circ)
    # print("Above min fill:", above_min_fill)
    # print("------------------")
    # print("Red mean:", color_feat['mean_rgb'][0])
    # print("Above red mean:", above_red_mean)
    # # print("Red dominant pct:", red_dominant)
    # print("Size:", size)
    # print("Is right size for nail:", is_right_size_for_nail)

    if is_red and is_round and is_right_size_for_nail:
        print("Classified as Type 2")
        return ("Type 2", "Red Nail")
    
    # Type 1: Silver Herring (metallic gray, larger or medium fragments)
    # Color signature: bluish-gray, low saturation
    # Shape: not extremely elongated (aspect ratio < 1.5)
    mean_r, mean_g, mean_b = color_feat['mean_rgb']
    is_metallic = (color_feat['hsv'][1] < 0.3 and  # Low saturation
                   mean_b >= mean_r * 0.9)          # Bluish tint
    
    is_valid_shape = shape_feat['aspect_ratio'] < TYPE1_MAX_ASPECT_RATIO
    
    if is_metallic and is_valid_shape and size >= TYPE1_MIN_SIZE:
        print("Classified as Type 1")
        return ("Type 1", "Silver Herring")
    
    print("Not classified")
    return None


def find_and_classify_markers(rgb, mask):
    """
    Find all marker objects and classify them.
    
    Returns: List of dicts with object info and classification
    """
    marker_mask = (mask == MARKER_CLASS).astype(np.uint8)
    labeled_array, num_features = ndimage.label(marker_mask)
    
    markers = []
    
    for obj_id in range(1, num_features + 1):
        obj_mask = (labeled_array == obj_id)
        
        shape_feat = compute_shape_features(obj_mask)
        if shape_feat is None:
            continue
            
        color_feat = compute_color_features(rgb, obj_mask)
        print("-------------------")
        print("Object ID:", obj_id)
        classification = classify_marker(shape_feat, color_feat)
        
        markers.append({
            'id': obj_id,
            'mask': obj_mask,
            'shape': shape_feat,
            'color': color_feat,
            'classification': classification,
        })

        print("-------------------")
    
    return markers


def group_nearby_fragments(markers, max_distance=500):
    """
    Group Type 1 markers that are close together (likely same herring).
    
    Returns: List of groups, each group is a list of marker indices
    """
    type1_indices = [i for i, m in enumerate(markers) 
                     if m['classification'] and m['classification'][0] == "Type 1"]
    
    if not type1_indices:
        return []
    
    # Simple clustering: group markers within max_distance
    groups = []
    used = set()
    
    for i in type1_indices:
        if i in used:
            continue
            
        group = [i]
        used.add(i)
        center_i = markers[i]['shape']['center']
        
        for j in type1_indices:
            if j in used:
                continue
            center_j = markers[j]['shape']['center']
            dist = np.sqrt((center_i[0] - center_j[0])**2 + 
                          (center_i[1] - center_j[1])**2)
            if dist < max_distance:
                group.append(j)
                used.add(j)
        
        groups.append(group)
    
    return groups


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_visualization(rgb, markers, image_name, output_path):
    """Create and save visualization of detected markers."""
    
    valid_markers = [m for m in markers if m['classification'] is not None]
    
    if not valid_markers:
        print(f"  No valid markers found in {image_name}")
        return
    
    # Group Type 1 markers
    type1_groups = group_nearby_fragments(markers)
    type2_markers = [m for m in valid_markers if m['classification'][0] == "Type 2"]
    
    # Calculate grid size: 1 for overview + 1 per Type 1 group + 1 per Type 2
    num_panels = 1 + len(type1_groups) + len(type2_markers)
    cols = min(3, num_panels)
    rows = (num_panels + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 7 * rows))
    if num_panels == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    # Panel 1: Full image with overlay
    ax = axes[0]
    display = rgb[::4, ::4].copy()
    
    for m in valid_markers:
        mask_small = m['mask'][::4, ::4]
        if m['classification'][0] == "Type 1":
            display[mask_small] = [0, 255, 255]  # Cyan for Type 1
        else:
            display[mask_small] = [255, 255, 0]  # Yellow for Type 2
    
    ax.imshow(display)
    ax.set_title(f'{image_name}\nCyan = Type 1 (Herring), Yellow = Type 2 (Nail)', 
                 fontsize=12, fontweight='bold')
    ax.axis('off')
    
    panel_idx = 1
    
    # Panels for Type 1 groups
    for group_idx, group in enumerate(type1_groups):
        if panel_idx >= len(axes):
            break
            
        ax = axes[panel_idx]
        panel_idx += 1
        
        # Get bounding box for group
        all_y, all_x = [], []
        total_pixels = 0
        for m_idx in group:
            m = markers[m_idx]
            coords = np.where(m['mask'])
            all_y.extend(coords[0])
            all_x.extend(coords[1])
            total_pixels += m['shape']['size']
        
        pad = 80
        y_min = max(0, min(all_y) - pad)
        y_max = min(rgb.shape[0], max(all_y) + pad)
        x_min = max(0, min(all_x) - pad)
        x_max = min(rgb.shape[1], max(all_x) + pad)
        
        rgb_crop = rgb[y_min:y_max, x_min:x_max].copy()
        
        # Draw contours for all fragments in group
        for m_idx in group:
            m = markers[m_idx]
            mask_crop = m['mask'][y_min:y_max, x_min:x_max]
            contour = ndimage.binary_dilation(mask_crop, iterations=3) ^ mask_crop
            rgb_crop[contour] = [0, 255, 255]
        
        ax.imshow(rgb_crop)
        
        fragment_ids = [markers[i]['id'] for i in group]
        ax.set_title(f'Type 1: Silver Herring\nFragments: {fragment_ids}\nTotal: {total_pixels:,} px', 
                     fontsize=11, fontweight='bold')
        ax.axis('off')
    
    # Panels for Type 2 markers
    for m in type2_markers:
        if panel_idx >= len(axes):
            break
            
        ax = axes[panel_idx]
        panel_idx += 1
        
        coords = np.where(m['mask'])
        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()
        
        pad = 80
        y1, y2 = max(0, y_min - pad), min(rgb.shape[0], y_max + pad)
        x1, x2 = max(0, x_min - pad), min(rgb.shape[1], x_max + pad)
        
        rgb_crop = rgb[y1:y2, x1:x2].copy()
        mask_crop = m['mask'][y1:y2, x1:x2]
        contour = ndimage.binary_dilation(mask_crop, iterations=3) ^ mask_crop
        rgb_crop[contour] = [255, 255, 0]
        
        ax.imshow(rgb_crop)
        
        r, g, b = m['color']['mean_rgb']
        ax.set_title(f"Type 2: Red Nail (Obj {m['id']})\n{m['shape']['size']:,} px | RGB({r:.0f},{g:.0f},{b:.0f})", 
                     fontsize=11, fontweight='bold')
        ax.axis('off')
    
    # Hide unused axes
    for i in range(panel_idx, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def print_summary(markers, image_name):
    """Print summary of detected markers."""
    valid = [m for m in markers if m['classification'] is not None]
    
    type1 = [m for m in valid if m['classification'][0] == "Type 1"]
    type2 = [m for m in valid if m['classification'][0] == "Type 2"]
    rejected = [m for m in markers if m['classification'] is None]
    
    print(f"\n  Results for {image_name}:")
    print(f"    Type 1 (Silver Herring): {len(type1)} fragments, {sum(m['shape']['size'] for m in type1):,} px total")
    for m in type1:
        r, g, b = m['color']['mean_rgb']
        print(f"      - Object {m['id']}: {m['shape']['size']:,} px, RGB({r:.0f},{g:.0f},{b:.0f})")
    
    print(f"    Type 2 (Red Nail): {len(type2)} markers")
    for m in type2:
        r, g, b = m['color']['mean_rgb']
        print(f"      - Object {m['id']}: {m['shape']['size']:,} px, RGB({r:.0f},{g:.0f},{b:.0f})")
    
    print(f"    Rejected: {len(rejected)} objects (size < {MIN_SIZE_PIXELS} or unclassified)")


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_folder(image_folder, mask_folder, output_folder):
    """Process all image/mask pairs in the folders."""
    
    image_folder = Path(image_folder)
    mask_folder = Path(mask_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    # image_extensions = ['.jpg', '.JPG', '.jpeg', '.JPEG']
    image_extensions = ['.JPG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(image_folder.glob(f'*{ext}'))
    
    print(f"Found {len(image_files)} images in {image_folder}")
    
    for image_path in sorted(image_files):
        # Find corresponding mask
        base_name = image_path.stem  # e.g., "1_1" from "1_1.JPG"
        mask_path = mask_folder / f"{base_name}_mask.png"
        
        if not mask_path.exists():
            print(f"  Skipping {image_path.name}: mask not found ({mask_path.name})")
            continue
        
        print(f"\nProcessing: {image_path.name}")
        
        try:
            # Load and align
            rgb, mask, rotation_k = load_and_align_images(image_path, mask_path)
            print(f"  Loaded: {rgb.shape}, rotation k={rotation_k}")
            
            # Find and classify markers
            markers = find_and_classify_markers(rgb, mask)
            print(f"  Found {len(markers)} marker objects")
            
            # Print summary
            print_summary(markers, image_path.name)
            
            # Create visualization
            output_path = output_folder / f"{base_name}_markers.png"
            create_visualization(rgb, markers, image_path.name, output_path)
            print(f"  Saved: {output_path}")
            
        except Exception as e:
            print(f"  Error processing {image_path.name}: {e}")
            import traceback
            traceback.print_exc()


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    process_folder(IMAGE_FOLDER, MASK_FOLDER, OUTPUT_FOLDER)
    print("\nDone!")