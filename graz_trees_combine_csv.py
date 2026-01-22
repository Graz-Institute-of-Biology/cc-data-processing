#!/usr/bin/env python3
"""
CSV Combiner with Folder Processing

This script finds all CSV files in a specified folder and combines them into a single CSV file,
adding a 'TrafficLevel' column based on the number in the filename.

Usage:
    python csv_combiner_folder.py output.csv input_folder

Example:
    python csv_combiner_folder.py combined_trees.csv ./tree_data
"""

import csv
import sys
import os
import re
import glob


def extract_traffic_level(filename):
    """
    Extract the traffic level from the filename.
    
    Args:
        filename (str): The filename to extract traffic level from
        
    Returns:
        int: Traffic level (1, 2, or 3) or None if not found
    """
    # Extract the number before .csv
    match = re.search(r'_(\d+)\.csv$', filename)
    if match:
        return int(match.group(1))
    return None


def get_traffic_description(level):
    """
    Get a descriptive text for the traffic level.
    
    Args:
        level (int): Traffic level (1, 2, or 3)
        
    Returns:
        str: Text description of traffic level
    """
    if level == 1:
        return "Low"
    elif level == 2:
        return "Medium"
    elif level == 3:
        return "High"
    return "Unknown"


def get_location_name(filename):
    """
    Extract the location name from the filename.
    
    Args:
        filename (str): The filename to extract location from
        
    Returns:
        str: Location name
    """
    # Extract the name before _number.csv
    match = re.search(r'([^/\\]+)_\d+\.csv$', os.path.basename(filename))
    if match:
        return match.group(1).capitalize()
    return "Unknown"


def combine_csv_files_in_folder(output_file, input_folder):
    """
    Find and combine all CSV files in a folder into a single CSV file.
    
    Args:
        output_file (str): Path to the output CSV file
        input_folder (str): Path to the folder containing CSV files
    """
    # Check if the input folder exists
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return False
    
    # Find all CSV files in the folder
    csv_pattern = os.path.join(input_folder, "*.csv")
    input_files = glob.glob(csv_pattern)
    
    if not input_files:
        print(f"Error: No CSV files found in '{input_folder}'.")
        return False
    
    print(f"Found {len(input_files)} CSV files in '{input_folder}':")
    for file in input_files:
        print(f"  - {os.path.basename(file)}")
    
    # Initialize counters
    total_records = 0
    files_processed = 0
    
    try:
        # Open the output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = None
            
            # Process each input file
            for input_file in input_files:
                # Extract traffic level from filename
                traffic_level = extract_traffic_level(input_file)
                if traffic_level is None:
                    print(f"Warning: Could not extract traffic level from '{os.path.basename(input_file)}'. Skipping.")
                    continue
                
                # Get location name
                location = get_location_name(input_file)
                
                # Get traffic description
                traffic_desc = get_traffic_description(traffic_level)
                
                # Read the input file
                with open(input_file, 'r', encoding='utf-8') as infile:
                    reader = csv.reader(infile)
                    
                    # Read header row
                    try:
                        header = next(reader)
                    except StopIteration:
                        print(f"Warning: '{os.path.basename(input_file)}' appears to be empty. Skipping.")
                        continue
                    
                    # For the first file, create the output header with additional columns
                    if writer is None:
                        new_header = header + ['Location', 'TrafficLevel', 'TrafficDescription']
                        writer = csv.writer(outfile)
                        writer.writerow(new_header)
                    
                    # Process each row in the input file
                    file_records = 0
                    for row in reader:
                        # Add location and traffic information
                        new_row = row + [location, str(traffic_level), traffic_desc]
                        writer.writerow(new_row)
                        file_records += 1
                
                print(f"Processed '{os.path.basename(input_file)}': {file_records} records")
                total_records += file_records
                files_processed += 1
        
        print(f"\nCombination completed successfully!")
        print(f"Files processed: {files_processed}")
        print(f"Total records combined: {total_records}")
        print(f"Output file: {output_file}")
        
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return False
    
    return True


def main():
    # Check if correct number of arguments provided
    # if len(sys.argv) != 3:
    #     print("Usage: python csv_combiner_folder.py output.csv input_folder")
    #     return
    
    output_file = "trees_graz.csv"
    input_folder = "trees_data"
    
    # Combine the files
    combine_csv_files_in_folder(output_file, input_folder)


if __name__ == "__main__":
    main()