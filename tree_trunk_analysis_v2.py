"""
Tree Stem Measurement Tool
==========================
Measures tree stem width and height from drone images with removed background.

Uses:
- Centerline calculation (center of mass per row)
- Perpendicular width measurement
- Arc length for height along curved stems
- DJI Mavic camera parameters for pixel-to-cm conversion

Author: Generated with Claude
"""

import numpy as np
from skimage import io, color, morphology
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
import math
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

# DJI Mavic 3 camera parameters
HORIZONTAL_FOV = 84  # degrees
VERTICAL_FOV = 67    # degrees (for 4:3 sensor aspect ratio)

# Distance assumptions (meters)
DEFAULT_DISTANCE = 1.00
MIN_DISTANCE = 0.80
MAX_DISTANCE = 1.20

# Image processing parameters
MASK_THRESHOLD = 0.05  # Threshold for background separation
MIN_OBJECT_SIZE = 1000  # Minimum pixels to be considered stem
CENTERLINE_SMOOTHING_SIGMA = 20  # Smoothing for centerline


# =============================================================================
# MEASUREMENT FUNCTIONS
# =============================================================================

def calculate_diameter(trunk_width_pixels, img_width, distance_m, fov_degrees=HORIZONTAL_FOV):
    """
    Calculate trunk diameter in cm given shooting distance.
    
    Parameters
    ----------
    trunk_width_pixels : float
        Width of trunk in pixels
    img_width : int
        Image width in pixels
    distance_m : float
        Distance from drone to tree in meters
    fov_degrees : float
        Horizontal field of view in degrees (default: 84° for DJI Mavic)
    
    Returns
    -------
    float
        Diameter in centimeters
    """
    frame_width_m = 2 * distance_m * math.tan(math.radians(fov_degrees / 2))
    pixels_per_meter = img_width / frame_width_m
    diameter_cm = (trunk_width_pixels / pixels_per_meter) * 100
    return diameter_cm


def calculate_height(trunk_height_pixels, img_height, distance_m, fov_degrees=VERTICAL_FOV):
    """
    Calculate trunk height in cm given shooting distance using vertical FOV.
    
    Parameters
    ----------
    trunk_height_pixels : float
        Height of trunk in pixels (arc length along centerline)
    img_height : int
        Image height in pixels
    distance_m : float
        Distance from drone to tree in meters
    fov_degrees : float
        Vertical field of view in degrees (default: 67° for 4:3 sensor)
    
    Returns
    -------
    float
        Height in centimeters
    """
    frame_height_m = 2 * distance_m * math.tan(math.radians(fov_degrees / 2))
    pixels_per_meter_vertical = img_height / frame_height_m
    height_cm = (trunk_height_pixels / pixels_per_meter_vertical) * 100
    return height_cm


def measure_perpendicular_width(mask, center_x, center_y, direction_x, direction_y, max_dist=2000):
    """
    Measure width perpendicular to the given direction at the center point.
    
    Parameters
    ----------
    mask : ndarray
        Binary mask of the stem
    center_x, center_y : float
        Center point coordinates
    direction_x, direction_y : float
        Direction vector (tangent to centerline)
    max_dist : int
        Maximum search distance in pixels
    
    Returns
    -------
    tuple
        (total_width, (edge1_x, edge1_y), (edge2_x, edge2_y))
    """
    # Perpendicular direction (rotate 90 degrees)
    perp_x = -direction_y
    perp_y = direction_x
    
    # Normalize
    length = np.sqrt(perp_x**2 + perp_y**2)
    if length == 0:
        return 0, (center_x, center_y), (center_x, center_y)
    perp_x /= length
    perp_y /= length
    
    h, w = mask.shape
    
    # Search in positive perpendicular direction
    dist_pos = 0
    for d in range(1, max_dist):
        px = int(round(center_x + perp_x * d))
        py = int(round(center_y + perp_y * d))
        if px < 0 or px >= w or py < 0 or py >= h or not mask[py, px]:
            dist_pos = d - 1
            break
    
    # Search in negative perpendicular direction
    dist_neg = 0
    for d in range(1, max_dist):
        px = int(round(center_x - perp_x * d))
        py = int(round(center_y - perp_y * d))
        if px < 0 or px >= w or py < 0 or py >= h or not mask[py, px]:
            dist_neg = d - 1
            break
    
    total_width = dist_pos + dist_neg
    
    # Edge points
    edge1_x = center_x + perp_x * dist_pos
    edge1_y = center_y + perp_y * dist_pos
    edge2_x = center_x - perp_x * dist_neg
    edge2_y = center_y - perp_y * dist_neg
    
    return total_width, (edge1_x, edge1_y), (edge2_x, edge2_y)


def calculate_centerline(binary_mask, min_pixels=10):
    """
    Calculate the centerline of the stem by finding center of mass per row.
    
    Parameters
    ----------
    binary_mask : ndarray
        Binary mask of the stem
    min_pixels : int
        Minimum pixels in a row to be considered valid
    
    Returns
    -------
    tuple
        (centerline_x, centerline_y, centerline_x_smooth)
    """
    img_height = binary_mask.shape[0]
    
    centerline_x = []
    centerline_y = []
    
    for row in range(img_height):
        row_pixels = np.where(binary_mask[row, :])[0]
        if len(row_pixels) >= min_pixels:
            left = row_pixels.min()
            right = row_pixels.max()
            center = (left + right) / 2
            centerline_x.append(center)
            centerline_y.append(row)
    
    centerline_x = np.array(centerline_x)
    centerline_y = np.array(centerline_y)
    
    # Smooth the centerline
    centerline_x_smooth = gaussian_filter1d(centerline_x, sigma=CENTERLINE_SMOOTHING_SIGMA)
    
    return centerline_x, centerline_y, centerline_x_smooth


def calculate_arc_length(centerline_x_smooth, centerline_y):
    """
    Calculate arc length along the centerline.
    
    Parameters
    ----------
    centerline_x_smooth : ndarray
        Smoothed x coordinates of centerline
    centerline_y : ndarray
        Y coordinates of centerline
    
    Returns
    -------
    float
        Arc length in pixels
    """
    arc_dx = np.diff(centerline_x_smooth)
    arc_dy = np.diff(centerline_y)
    arc_segments = np.sqrt(arc_dx**2 + arc_dy**2)
    return np.sum(arc_segments)


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_stem(image_path, 
                 distance_m=DEFAULT_DISTANCE,
                 min_distance_m=MIN_DISTANCE,
                 max_distance_m=MAX_DISTANCE,
                 measurement_position=0.5,
                 save_plot=True,
                 output_path=None,
                 show_plot=False):
    """
    Analyze a tree stem image and calculate width and height.
    
    Parameters
    ----------
    image_path : str or Path
        Path to the input image (background should be removed/black)
    distance_m : float
        Assumed distance from drone to tree in meters
    min_distance_m : float
        Minimum assumed distance for range calculation
    max_distance_m : float
        Maximum assumed distance for range calculation
    measurement_position : float
        Position along stem for width measurement (0.0 = top, 1.0 = bottom)
    save_plot : bool
        Whether to save the visualization
    output_path : str or Path, optional
        Path for output image. If None, uses input name + '_analysis.png'
    show_plot : bool
        Whether to display the plot
    
    Returns
    -------
    dict
        Dictionary containing all measurements
    """
    # Load image
    image_path = Path(image_path)
    img = io.imread(image_path)
    img_height, img_width = img.shape[:2]
    
    # Create binary mask
    if len(img.shape) == 3:
        gray = color.rgb2gray(img)
    else:
        gray = img
    
    binary_mask = gray > MASK_THRESHOLD
    binary_mask = morphology.remove_small_objects(binary_mask, min_size=MIN_OBJECT_SIZE)
    
    # Calculate centerline
    centerline_x, centerline_y, centerline_x_smooth = calculate_centerline(binary_mask)
    
    if len(centerline_x) == 0:
        raise ValueError("No stem detected in image")
    
    # Calculate local direction (tangent) at each point
    dx = np.gradient(centerline_x_smooth)
    dy = np.gradient(centerline_y)
    
    # Measure perpendicular width at specified position
    measure_idx = int(len(centerline_y) * measurement_position)
    measure_idx = max(0, min(measure_idx, len(centerline_y) - 1))
    
    measure_y = centerline_y[measure_idx]
    measure_x = centerline_x_smooth[measure_idx]
    dir_x = dx[measure_idx]
    dir_y = dy[measure_idx]
    
    width_px, edge1, edge2 = measure_perpendicular_width(
        binary_mask, measure_x, measure_y, dir_x, dir_y
    )
    
    # Calculate arc length (height)
    arc_length_px = calculate_arc_length(centerline_x_smooth, centerline_y)
    
    # Calculate measurements in cm for all distances
    diameter_cm = calculate_diameter(width_px, img_width, distance_m)
    diameter_cm_min = calculate_diameter(width_px, img_width, min_distance_m)
    diameter_cm_max = calculate_diameter(width_px, img_width, max_distance_m)
    
    height_cm = calculate_height(arc_length_px, img_height, distance_m)
    height_cm_min = calculate_height(arc_length_px, img_height, min_distance_m)
    height_cm_max = calculate_height(arc_length_px, img_height, max_distance_m)
    
    # Compile results
    results = {
        'image_path': str(image_path),
        'image_width_px': img_width,
        'image_height_px': img_height,
        'stem_width_px': width_px,
        'stem_height_px': arc_length_px,
        'stem_width_cm': diameter_cm,
        'stem_width_cm_min': diameter_cm_min,
        'stem_width_cm_max': diameter_cm_max,
        'stem_height_cm': height_cm,
        'stem_height_cm_min': height_cm_min,
        'stem_height_cm_max': height_cm_max,
        'distance_m': distance_m,
        'min_distance_m': min_distance_m,
        'max_distance_m': max_distance_m,
        'measurement_position': measurement_position,
        'centerline_x': centerline_x_smooth,
        'centerline_y': centerline_y,
        'measurement_point': (measure_x, measure_y),
        'edge_points': (edge1, edge2),
    }
    
    # Create visualization
    if save_plot or show_plot:
        fig, axes = plt.subplots(1, 2, figsize=(20, 14))
        
        # Panel 1: Original image
        axes[0].imshow(img)
        axes[0].set_title('Original Image', fontsize=16)
        axes[0].axis('off')
        
        # Panel 2: Original + centerline + perpendicular diameter line
        axes[1].imshow(img)
        
        # Draw centerline
        axes[1].plot(centerline_x_smooth, centerline_y, 
                     color='red', linewidth=4, label='Centerline')
        
        # Draw perpendicular diameter measurement line
        axes[1].plot([edge1[0], edge2[0]], [edge1[1], edge2[1]], 
                     color='cyan', linewidth=6, solid_capstyle='round', 
                     label='Diameter (perpendicular)')
        
        # Add markers at the edge points
        axes[1].plot(edge1[0], edge1[1], 'o', color='yellow', markersize=18, 
                     markeredgecolor='black', markeredgewidth=3)
        axes[1].plot(edge2[0], edge2[1], 'o', color='yellow', markersize=18, 
                     markeredgecolor='black', markeredgewidth=3)
        
        # Mark the center point
        axes[1].plot(measure_x, measure_y, 's', color='lime', markersize=14, 
                     markeredgecolor='black', markeredgewidth=2, label='Center')
        
        axes[1].set_title('Centerline + Perpendicular Diameter', fontsize=16)
        axes[1].axis('off')
        axes[1].legend(loc='lower right', fontsize=12)
        
        # Main title with measurements
        fig.suptitle(
            f'Stem Analysis\n'
            f'(assuming distance = {distance_m:.2f}m ({min_distance_m:.1f}m - {max_distance_m:.1f}m), '
            f'FOV = {HORIZONTAL_FOV}° horiz / {VERTICAL_FOV}° vert)\n'
            f'Width: {width_px:.0f} px = {diameter_cm:.1f} cm ({diameter_cm_min:.1f} - {diameter_cm_max:.1f} cm)  |  '
            f'Height: {arc_length_px:.0f} px = {height_cm:.1f} cm ({height_cm_min:.1f} - {height_cm_max:.1f} cm)',
            fontsize=16, fontweight='bold', y=0.98
        )
        
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        
        if save_plot:
            if output_path is None:
                output_path = image_path.parent / f"{image_path.stem}_analysis.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            results['output_path'] = str(output_path)
            print(f"Saved: {output_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    return results


def analyze_multiple_stems(image_paths, output_dir=None, **kwargs):
    """
    Analyze multiple stem images.
    
    Parameters
    ----------
    image_paths : list
        List of paths to input images
    output_dir : str or Path, optional
        Directory for output files. If None, saves next to input files.
    **kwargs
        Additional arguments passed to analyze_stem()
    
    Returns
    -------
    list
        List of result dictionaries
    """
    all_results = []
    
    for image_path in image_paths:
        image_path = Path(image_path)
        print(f"\nProcessing: {image_path.name}")
        
        try:
            if output_dir:
                output_path = Path(output_dir) / f"{image_path.stem}_analysis.png"
            else:
                output_path = None
            
            results = analyze_stem(image_path, output_path=output_path, **kwargs)
            all_results.append(results)
            
            print(f"  Width:  {results['stem_width_cm']:.1f} cm "
                  f"({results['stem_width_cm_min']:.1f} - {results['stem_width_cm_max']:.1f} cm)")
            print(f"  Height: {results['stem_height_cm']:.1f} cm "
                  f"({results['stem_height_cm_min']:.1f} - {results['stem_height_cm_max']:.1f} cm)")
            
        except Exception as e:
            print(f"  Error: {e}")
            all_results.append({'image_path': str(image_path), 'error': str(e)})
    
    return all_results


def results_to_csv(results, output_path):
    """
    Export results to CSV file.
    
    Parameters
    ----------
    results : list
        List of result dictionaries from analyze_stem() or analyze_multiple_stems()
    output_path : str or Path
        Path for output CSV file
    """
    import csv
    
    fieldnames = [
        'image_path', 
        'stem_width_px', 'stem_height_px',
        'stem_width_cm', 'stem_width_cm_min', 'stem_width_cm_max',
        'stem_height_cm', 'stem_height_cm_min', 'stem_height_cm_max',
        'distance_m', 'min_distance_m', 'max_distance_m',
        'error'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"\nResults saved to: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Measure tree stem width and height from drone images')
    parser.add_argument('images', nargs='+', help='Input image path(s)')
    parser.add_argument('-d', '--distance', type=float, default=DEFAULT_DISTANCE,
                        help=f'Assumed distance in meters (default: {DEFAULT_DISTANCE})')
    parser.add_argument('--min-distance', type=float, default=MIN_DISTANCE,
                        help=f'Minimum distance for range (default: {MIN_DISTANCE})')
    parser.add_argument('--max-distance', type=float, default=MAX_DISTANCE,
                        help=f'Maximum distance for range (default: {MAX_DISTANCE})')
    parser.add_argument('-o', '--output-dir', type=str, default=None,
                        help='Output directory for analysis images')
    parser.add_argument('--csv', type=str, default=None,
                        help='Output CSV file path')
    parser.add_argument('--no-plot', action='store_true',
                        help='Skip saving visualization plots')
    parser.add_argument('--show', action='store_true',
                        help='Display plots interactively')
    
    args = parser.parse_args()
    
    # Process images
    results = analyze_multiple_stems(
        args.images,
        output_dir=args.output_dir,
        distance_m=args.distance,
        min_distance_m=args.min_distance,
        max_distance_m=args.max_distance,
        save_plot=not args.no_plot,
        show_plot=args.show
    )
    