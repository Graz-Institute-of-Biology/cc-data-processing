#!/usr/bin/env python3
"""
Tree Trunk Diameter Analysis using Sharpness + Regionprops
Works on full DJI Mavic 3 images without manual ROI selection
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure, morphology, filters
from skimage.color import rgb2gray, label2rgb
from scipy import ndimage
from scipy.ndimage import gaussian_filter
from PIL import Image
import math
import sys

def calculate_sharpness_map(img_gray, sigma=5):
    """Calculate normalized sharpness map using Laplacian"""
    laplacian = ndimage.laplace(img_gray)
    sharpness_map = np.abs(laplacian)
    sharpness_smooth = gaussian_filter(sharpness_map, sigma=sigma)
    
    # Normalize to 0-1
    sharpness_normalized = (sharpness_smooth - sharpness_smooth.min()) / (sharpness_smooth.max() - sharpness_smooth.min())
    return sharpness_normalized

def calculate_dynamic_threshold(sharpness_map, method='percentile', percentile=75, plot=False):
    """
    Calculate dynamic sharpness threshold based on image histogram
    
    Parameters:
    -----------
    sharpness_map : numpy array
        Normalized sharpness map (0-1)
    method : str
        Method to use: 'percentile', 'otsu', 'mean_std', 'knee'
    percentile : float
        Percentile to use if method='percentile' (e.g., 75 = keep top 25%)
    plot : bool
        Whether to create histogram plot
    
    Returns:
    --------
    threshold : float
        Calculated threshold value
    method_info : dict
        Information about the threshold calculation
    """
    
    flat_sharpness = sharpness_map.flatten()
    
    if method == 'percentile':
        # Use percentile - keep the sharpest X% of pixels
        threshold = np.percentile(flat_sharpness, percentile)
        method_info = {
            'method': 'percentile',
            'percentile': percentile,
            'threshold': threshold,
            'pixels_above': np.sum(sharpness_map > threshold),
            'percent_above': (np.sum(sharpness_map > threshold) / sharpness_map.size) * 100
        }
    
    elif method == 'otsu':
        # Use Otsu's method for automatic thresholding
        threshold = filters.threshold_otsu(sharpness_map)
        method_info = {
            'method': 'otsu',
            'threshold': threshold,
            'pixels_above': np.sum(sharpness_map > threshold),
            'percent_above': (np.sum(sharpness_map > threshold) / sharpness_map.size) * 100
        }
    
    elif method == 'mean_std':
        # Use mean + standard deviation
        mean_sharp = np.mean(flat_sharpness)
        std_sharp = np.std(flat_sharpness)
        threshold = mean_sharp + 0.5 * std_sharp  # Adjustable multiplier
        method_info = {
            'method': 'mean_std',
            'mean': mean_sharp,
            'std': std_sharp,
            'threshold': threshold,
            'pixels_above': np.sum(sharpness_map > threshold),
            'percent_above': (np.sum(sharpness_map > threshold) / sharpness_map.size) * 100
        }
    
    elif method == 'knee':
        # Find the "knee" in the cumulative histogram
        hist, bin_edges = np.histogram(flat_sharpness, bins=100)
        cumsum = np.cumsum(hist)
        cumsum_norm = cumsum / cumsum[-1]
        
        # Find knee point (where cumulative curve starts to flatten)
        # Use second derivative
        gradient = np.gradient(cumsum_norm)
        gradient2 = np.gradient(gradient)
        knee_idx = np.argmax(np.abs(gradient2[20:80])) + 20  # Focus on middle range
        threshold = bin_edges[knee_idx]
        
        method_info = {
            'method': 'knee',
            'knee_index': knee_idx,
            'threshold': threshold,
            'pixels_above': np.sum(sharpness_map > threshold),
            'percent_above': (np.sum(sharpness_map > threshold) / sharpness_map.size) * 100
        }
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Create histogram plot if requested
    if plot:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        axes[0].hist(flat_sharpness, bins=100, alpha=0.7, color='blue', edgecolor='black')
        axes[0].axvline(threshold, color='red', linewidth=3, linestyle='--', 
                       label=f'Threshold = {threshold:.3f}')
        axes[0].set_xlabel('Sharpness Value', fontsize=12)
        axes[0].set_ylabel('Frequency', fontsize=12)
        axes[0].set_title(f'Sharpness Histogram ({method} method)', fontsize=13, fontweight='bold')
        axes[0].legend(fontsize=11)
        axes[0].grid(alpha=0.3)
        
        # Cumulative histogram
        hist, bin_edges = np.histogram(flat_sharpness, bins=100)
        cumsum = np.cumsum(hist)
        cumsum_norm = cumsum / cumsum[-1] * 100
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        axes[1].plot(bin_centers, cumsum_norm, 'b-', linewidth=2)
        axes[1].axvline(threshold, color='red', linewidth=3, linestyle='--',
                       label=f'Threshold = {threshold:.3f}')
        axes[1].axhline(100 - method_info['percent_above'], color='red', 
                       linewidth=1, linestyle=':', alpha=0.5)
        axes[1].set_xlabel('Sharpness Value', fontsize=12)
        axes[1].set_ylabel('Cumulative Percentage', fontsize=12)
        axes[1].set_title('Cumulative Distribution', fontsize=13, fontweight='bold')
        axes[1].legend(fontsize=11)
        axes[1].grid(alpha=0.3)
        axes[1].set_ylim([0, 105])
        
        # Add text box with info
        info_text = f"Threshold: {threshold:.3f}\n"
        info_text += f"Pixels above: {method_info['pixels_above']:,}\n"
        info_text += f"Percentage: {method_info['percent_above']:.1f}%"
        axes[1].text(0.02, 0.98, info_text, transform=axes[1].transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        method_info['histogram_fig'] = fig
    
    return threshold, method_info

def find_trunk_region(labeled, regions, img_width, img_height):
    """Find the best trunk candidate from labeled regions"""
    
    trunk_candidates = []
    
    for region in regions:
        bbox = region.bbox  # (min_row, min_col, max_row, max_col)
        region_width = bbox[3] - bbox[1]
        region_height = bbox[2] - bbox[0]
        aspect_ratio = region_height / region_width if region_width > 0 else 0
        
        # Trunk criteria:
        # - Vertical orientation (aspect > 0.8)
        # - Reasonable width (100-700 pixels for tree at ~1m)
        # - Substantial height (> 200 pixels)
        # - Good size (> 5000 pixels)
        # - Good solidity (compact shape)

        # print(f"Region {region.label}:")
        # print(f"  width={region_width}") 
        # print(f"  height={region_height}")
        # print(f"  aspect={aspect_ratio:.2f}")
        # print(f"  area={region.area}")
        # print(f"  solidity={region.solidity:.2f}")
        
        if (0.9 < aspect_ratio < 5.0 and
            50 < region_width < 1500 and
            region_height > 200 and
            region.area > 500 and
            region.solidity > 0.6):
            
            trunk_candidates.append({
                'label': region.label,
                'region': region,
                'width': region_width,
                'height': region_height,
                'bbox': bbox,
                'area': region.area,
                'intensity': region.mean_intensity,
                'aspect': aspect_ratio,
                'solidity': region.solidity,
                'centroid': region.centroid
            })
    
    if not trunk_candidates:
        return None
    
    # Score candidates: prefer large area, good aspect ratio, high solidity
    for cand in trunk_candidates:
        score = (cand['area'] / 1000 +  # Size important
                 cand['intensity'] * 5 +  # Brightness important
                 cand['solidity'] * 3 +  # Compactness important
                 min(cand['aspect'] / 1.5, 2.0))  # Prefer aspect ~1.5
        cand['score'] = score
    
    # Return best candidate
    best_trunk = max(trunk_candidates, key=lambda x: x['score'])
    return best_trunk

def calculate_diameter(trunk_width_pixels, img_width, distance_m, fov_degrees=84):
    """Calculate trunk diameter in cm given shooting distance"""
    frame_width_m = 2 * distance_m * math.tan(math.radians(fov_degrees / 2))
    pixels_per_meter = img_width / frame_width_m
    diameter_cm = (trunk_width_pixels / pixels_per_meter) * 100
    return diameter_cm

def analyze_trunk(image_path, threshold_method='percentile', threshold_percentile=75, 
                  manual_threshold=None, output_dir='./'):
    """
    Main analysis function
    
    Parameters:
    -----------
    image_path : str
        Path to the DJI Mavic 3 image
    threshold_method : str
        Method for dynamic threshold: 'percentile', 'otsu', 'mean_std', 'knee'
        Set to None to use manual_threshold
    threshold_percentile : float
        Percentile for 'percentile' method (e.g., 75 = keep top 25%)
    manual_threshold : float
        Manual threshold value (0.0-1.0). If provided, overrides threshold_method
    output_dir : str
        Directory to save output visualization
    
    Returns:
    --------
    dict with trunk measurements
    """
    
    # Load image
    print("="*70)
    print("TREE TRUNK DIAMETER ANALYSIS")
    print("="*70)
    print(f"\nLoading image: {image_path}")
    
    input_file = os.path.splitext(os.path.basename(image_path))[0]
    img = Image.open(image_path)
    img_array = np.array(img)
    height, width, _ = img_array.shape
    
    print(f"Image dimensions: {width} x {height} pixels")
    
    # Convert to grayscale
    img_gray = rgb2gray(img_array)
    
    # Calculate sharpness map
    print(f"\nCalculating sharpness map...")
    sharpness_map = calculate_sharpness_map(img_gray, sigma=5)
    
    print(f"Sharpness statistics:")
    print(f"  Min: {sharpness_map.min():.3f}")
    print(f"  Max: {sharpness_map.max():.3f}")
    print(f"  Mean: {sharpness_map.mean():.3f}")
    print(f"  Median: {np.median(sharpness_map):.3f}")
    
    # Calculate threshold (dynamic or manual)
    if manual_threshold is not None:
        sharpness_threshold = manual_threshold
        threshold_info = {
            'method': 'manual',
            'threshold': sharpness_threshold,
            'pixels_above': np.sum(sharpness_map > sharpness_threshold),
            'percent_above': (np.sum(sharpness_map > sharpness_threshold) / sharpness_map.size) * 100
        }
        print(f"\nUsing manual threshold: {sharpness_threshold:.3f}")
    else:
        print(f"\nCalculating dynamic threshold using '{threshold_method}' method...")
        sharpness_threshold, threshold_info = calculate_dynamic_threshold(
            sharpness_map, 
            method=threshold_method,
            percentile=threshold_percentile,
            plot=True
        )
        print(f"Dynamic threshold calculated: {sharpness_threshold:.3f}")
    
    print(f"Pixels above threshold: {threshold_info['pixels_above']:,} ({threshold_info['percent_above']:.1f}%)")
    
    # Apply sharpness threshold
    sharp_mask = sharpness_map > sharpness_threshold
    
    # Clean up the mask
    sharp_mask_clean = morphology.remove_small_objects(sharp_mask, min_size=500)
    sharp_mask_clean = morphology.binary_closing(sharp_mask_clean, morphology.disk(5))
    sharp_mask_clean = morphology.remove_small_holes(sharp_mask_clean, area_threshold=500)
    
    # Label sharp regions
    labeled = measure.label(sharp_mask_clean)
    print(f"Found {labeled.max()} sharp regions")
    
    if labeled.max() == 0:
        print("ERROR: No sharp regions found. Try lowering the sharpness threshold.")
        return None
    
    # Get regionprops
    regions = measure.regionprops(labeled, intensity_image=img_gray)
    
    # Find best trunk candidate
    print(f"\nAnalyzing regions to find trunk...")
    best_trunk = find_trunk_region(labeled, regions, width, height)
    
    if best_trunk is None:
        print("ERROR: No suitable trunk candidate found.")
        return None
    
    # Extract results
    bbox = best_trunk['bbox']
    trunk_width_pixels = best_trunk['width']
    trunk_height_pixels = best_trunk['height']
    
    print(f"\n{'='*70}")
    print("TRUNK DETECTED")
    print(f"{'='*70}")
    print(f"Width: {trunk_width_pixels} pixels ({(trunk_width_pixels/width)*100:.2f}%)")
    print(f"Height: {trunk_height_pixels} pixels")
    print(f"Area: {best_trunk['area']:.0f} pixels")
    print(f"Aspect ratio: {best_trunk['aspect']:.2f}")
    print(f"Solidity: {best_trunk['solidity']:.3f}")
    print(f"Bounding box (row_min, col_min, row_max, col_max): {bbox}")
    
    # Calculate diameters at different distances
    print(f"\n{'='*70}")
    print("DIAMETER CALCULATIONS")
    print(f"{'='*70}")
    
    distances = [0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]
    diameters = {}
    heights_cm = {}
    surface_areas = {}
    
    print(f"\n{'Distance':<12} {'Frame Width':<15} {'Trunk Diameter':<15} {'Trunk Height':<15}")
    print("-" * 68)
    
    for dist in distances:
        # Calculate diameter
        diameter = calculate_diameter(trunk_width_pixels, width, dist)
        diameters[dist] = diameter
        frame_width = 2 * dist * math.tan(math.radians(84 / 2))
        
        # Calculate height (using vertical FOV)
        # DJI Mavic 3 has 4:3 sensor aspect ratio
        # Horizontal FOV = 84°, so vertical FOV ≈ 67° (calculated from sensor aspect)
        vertical_fov = 67  # degrees (approximate for 4:3 sensor with 84° horizontal FOV)
        frame_height = 2 * dist * math.tan(math.radians(vertical_fov / 2))
        pixels_per_meter_vertical = height / frame_height
        height_cm = (trunk_height_pixels / pixels_per_meter_vertical) * 100
        heights_cm[dist] = height_cm
        
        # Calculate cylindrical surface area: A = 2*pi*r*(h+r)
        radius_cm = diameter / 2
        surface_area_cm2 = 2 * math.pi * radius_cm * (height_cm + radius_cm)
        surface_areas[dist] = surface_area_cm2
        
        print(f"{dist:.2f} m{'':<6} {frame_width:.3f} m{'':<7} {diameter:.1f} cm{'':<9} {height_cm:.1f} cm")
    
    # Best estimate at typical focus distance (0.8-1.2m)
    diam_08m = diameters[0.80]
    diam_12m = diameters[1.20]
    best_estimate_diameter = (diam_08m + diam_12m) / 2
    
    height_08m = heights_cm[0.80]
    height_12m = heights_cm[1.20]
    best_estimate_height = (height_08m + height_12m) / 2
    
    surface_08m = surface_areas[0.80]
    surface_12m = surface_areas[1.20]
    best_estimate_surface = (surface_08m + surface_12m) / 2
    
    print(f"\n{'='*70}")
    print("BEST ESTIMATE (at 0.8-1.2m with focus peaking):")
    print(f"{'='*70}")
    print(f"Diameter range: {diam_08m:.1f} - {diam_12m:.1f} cm (mean: {best_estimate_diameter:.1f} cm)")
    print(f"Height range: {height_08m:.1f} - {height_12m:.1f} cm (mean: {best_estimate_height:.1f} cm)")
    print(f"Surface area range: {surface_08m:.1f} - {surface_12m:.1f} cm² (mean: {best_estimate_surface:.1f} cm²)")
    
    # Create visualization
    print(f"\nGenerating visualization...")
    
    # Create main figure with 2 rows, 3 columns
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # ROW 1, COL 1: Original image
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(img_array)
    ax1.set_title('Original Image', fontsize=13, fontweight='bold')
    ax1.axis('off')
    
    # ROW 1, COL 2: Sharpness map
    ax2 = fig.add_subplot(gs[0, 1])
    im = ax2.imshow(sharpness_map, cmap='hot')
    ax2.set_title(f'Sharpness Map', fontsize=12)
    ax2.axis('off')
    plt.colorbar(im, ax=ax2, fraction=0.046)
    
    # ROW 1, COL 3: Histogram with threshold
    ax3 = fig.add_subplot(gs[0, 2])
    flat_sharpness = sharpness_map.flatten()
    ax3.hist(flat_sharpness, bins=100, alpha=0.7, color='blue', edgecolor='black')
    ax3.axvline(sharpness_threshold, color='red', linewidth=3, linestyle='--', 
               label=f'Threshold = {sharpness_threshold:.3f}')
    ax3.set_xlabel('Sharpness Value', fontsize=11)
    ax3.set_ylabel('Frequency', fontsize=11)
    ax3.set_title(f'Sharpness Histogram\n({threshold_info["method"].title()} Method)', fontsize=12)
    ax3.legend(fontsize=10)
    ax3.grid(alpha=0.3)
    
    # Add info text box
    info_text = f"Pixels above: {threshold_info['pixels_above']:,}\n"
    info_text += f"Percentage: {threshold_info['percent_above']:.1f}%"
    ax3.text(0.98, 0.97, info_text, transform=ax3.transAxes,
            fontsize=9, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # ROW 2, COL 1: Sharp regions mask
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.imshow(sharp_mask_clean, cmap='gray')
    ax4.set_title(f'Sharp Regions Mask\n({labeled.max()} regions)', fontsize=12)
    ax4.axis('off')
    
    # ROW 2, COL 2: Labeled regions
    ax5 = fig.add_subplot(gs[1, 1])
    label_img = label2rgb(labeled, image=img_gray, bg_label=0, alpha=0.5)
    ax5.imshow(label_img)
    ax5.set_title('Labeled Sharp Regions', fontsize=12)
    ax5.axis('off')
    
    # ROW 2, COL 3: Full image with detection and measurement line
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.imshow(img_array)
    
    # Draw bounding box
    rect = plt.Rectangle((bbox[1], bbox[0]), bbox[3] - bbox[1], bbox[2] - bbox[0],
                         fill=False, edgecolor='lime', linewidth=3)
    ax6.add_patch(rect)
    
    # Draw width measurement line at middle of trunk
    y_mid = bbox[0] + (bbox[2] - bbox[0]) // 2
    ax6.plot([bbox[1], bbox[3]], [y_mid, y_mid],
            'r-', linewidth=5, label=f'Width: {trunk_width_pixels} px')
    
    # Draw vertical markers at width edges
    ax6.plot([bbox[1], bbox[1]], [y_mid - 100, y_mid + 100],
            'r-', linewidth=3)
    ax6.plot([bbox[3], bbox[3]], [y_mid - 100, y_mid + 100],
            'r-', linewidth=3)
    
    # Draw height measurement line on the left side of trunk
    x_left = bbox[1] - 150  # Offset to the left
    ax6.plot([x_left, x_left], [bbox[0], bbox[2]],
            'b-', linewidth=5, label=f'Height: {trunk_height_pixels} px')
    
    # Draw horizontal markers at height edges
    ax6.plot([x_left - 100, x_left + 100], [bbox[0], bbox[0]],
            'b-', linewidth=3)
    ax6.plot([x_left - 100, x_left + 100], [bbox[2], bbox[2]],
            'b-', linewidth=3)
    
    ax6.legend(fontsize=11, loc='upper right')
    ax6.set_title('Full Image with Detection', fontsize=13, fontweight='bold')
    ax6.axis('off')
    
    # Add title with all measurements
    if threshold_info['method'] == 'manual':
        threshold_text = f"Manual Threshold={sharpness_threshold:.3f}"
    else:
        threshold_text = f"{threshold_info['method'].title()} Threshold={sharpness_threshold:.3f}"
    
    # Create multi-line title with all information
    title_line1 = f"Tree Trunk Analysis - {threshold_text}"
    title_line2 = f"Width: {trunk_width_pixels}px ({best_estimate_diameter:.1f} cm) | Height: {trunk_height_pixels}px ({best_estimate_height:.1f} cm)"
    title_line3 = f"Detected Area: {best_trunk['area']:,}px² | Cylinder Surface Area: {best_estimate_surface:.1f} cm²"
    
    plt.suptitle(f'{title_line1}\n{title_line2}\n{title_line3}', 
                 fontsize=13, fontweight='bold')
    
    # Save main visualization
    output_path = f"{output_dir}/{input_file}_trunk_analysis_result.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_path}")
    plt.close()
    
    # Also save a standalone detailed histogram if histogram was generated separately
    # if 'histogram_fig' in threshold_info:
    #     hist_output_path = f"{output_dir}/sharpness_histogram_detailed.png"
    #     threshold_info['histogram_fig'].savefig(hist_output_path, dpi=150, bbox_inches='tight')
    #     print(f"Detailed histogram saved to: {hist_output_path}")
    #     plt.close(threshold_info['histogram_fig'])
    
    # Return results
    results = {
        'trunk_width_pixels': trunk_width_pixels,
        'trunk_height_pixels': trunk_height_pixels,
        'bbox': bbox,
        'area': best_trunk['area'],
        'aspect_ratio': best_trunk['aspect'],
        'solidity': best_trunk['solidity'],
        'diameters_cm': diameters,
        'heights_cm': heights_cm,
        'surface_areas_cm2': surface_areas,
        'best_estimate_diameter_cm': best_estimate_diameter,
        'best_estimate_height_cm': best_estimate_height,
        'best_estimate_surface_cm2': best_estimate_surface,
        'diameter_range_cm': (diam_08m, diam_12m),
        'height_range_cm': (height_08m, height_12m),
        'surface_range_cm2': (surface_08m, surface_12m),
        'threshold_method': threshold_info['method'],
        'threshold_value': sharpness_threshold,
        'threshold_info': threshold_info
    }
    
    return results

def run_analysis(image_path):
    # Run analysis with different threshold methods
    # Options: 'percentile', 'otsu', 'mean_std', 'knee', or manual_threshold=0.1
    
        
    results = analyze_trunk(
        image_path=image_path,
        output_dir=r'C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing',
        threshold_method='otsu',
    )
    
    if results is None:
        print("Analysis (partly) failed.")
    else:
        print(f"\nResult: {results['trunk_width_pixels']}px = {results['best_estimate_diameter_cm']:.1f}cm")
        
        # Use percentile method as default recommendation
        best_result = results
        print(f"\nRecommended method: {best_result['threshold_method'].title()}")
        print(f"Trunk diameter: {best_result['best_estimate_diameter_cm']:.1f} cm")
        print(f"Range (0.8-1.2m): {best_result['diameter_range_cm'][0]:.1f} - {best_result['diameter_range_cm'][1]:.1f} cm")
        print(f"Trunk height: {best_result['best_estimate_height_cm']:.1f} cm")
        print(f"Surface area: {best_result['best_estimate_surface_cm2']:.1f} cm²")
        print(f"\nThis method keeps the top {100-best_result['threshold_info']['percent_above']:.0f}% sharpest regions")

        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)

if __name__ == "__main__":
    # Example usage
    # if len(sys.argv) > 1:
    #     image_path = sys.argv[1]
    # else:
    #     # Default to the uploaded image
    #     image_path = "/mnt/user-data/uploads/230223_TF_C_E_DJI_0753.JPG"


    base_dir = r"C:\Users\faulhamm\Documents\Philipp\training\active_learning_v11\ReChecks_Errors\TF\Foreground_background\tree_metrics_test"
    
    for img in os.listdir(base_dir):
        if img.endswith(".JPG") or img.endswith(".jpg") or img.endswith(".PNG") or img.endswith(".png"):
            image_path = os.path.join(base_dir, img)
            run_analysis(image_path)

    



    
    
