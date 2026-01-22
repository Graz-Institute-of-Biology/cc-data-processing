#!/usr/bin/env python3
"""
Tree Inventory Converter

This script converts a tab-delimited tree inventory text file to CSV format.
It handles special characters and ensures proper CSV formatting.

Usage:
    python tree_inventory_converter.py input.txt output.csv

Example:
    python tree_inventory_converter.py tree_data.txt tree_inventory.csv
"""

import csv
import sys
import os

def convert_tree_inventory(input_file, output_file):
    """
    Convert a tab-delimited tree inventory file to CSV format.
    
    Args:
        input_file (str): Path to the input tab-delimited file
        output_file (str): Path to the output CSV file
    """
    # Define the column headers
    headers = [
        "ID", 
        "LatinName", 
        "GermanName", 
        "Type", 
        "PlantingYear", 
        "RemovalYear", 
        "Notes", 
        "AdditionalNotes"
    ]
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Write to the output CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write the header row
            writer.writerow(headers)
            
            # Process each line
            for line in lines:
                # Split by tabs
                fields = line.strip().split('\t')
                
                # Ensure we have the right number of fields (pad with empty strings if needed)
                while len(fields) < len(headers):
                    fields.append('')
                
                # Write the row to the CSV
                writer.writerow(fields)
        
        print(f"Conversion completed successfully!")
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        print(f"Total records processed: {len(lines)}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return False
    except PermissionError:
        print(f"Error: Permission denied when trying to write to '{output_file}'.")
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return False
    
    return True

def main():
    # Check if correct number of arguments provided
    # if len(sys.argv) != 3:
    #     print("Usage: python tree_inventory_converter.py input.txt output.csv")
    #     return
    
    input_file = "grieskai.txt"
    output_file = input_file.replace('.txt', '.csv')
    
    # Check if input file exists
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
    
    # Convert the file
    convert_tree_inventory(input_file, output_file)

if __name__ == "__main__":
    main()