#!/usr/bin/env python3
"""
CSV to JSON Converter for eBay MTG Card Lister

This standalone script converts CSV files containing Magic: The Gathering card information
into JSON format compatible with the ebaylisterallinone.py script.

Supports multiple CSV formats:

1. Simple Format:
   name,set
   Sol Ring,Commander 2013

2. TCGplayer Format:
   Quantity,Name,Simple Name,Set,Card Number,Set Code,Printing,Condition,Language,Rarity,Product ID,SKU
   1,Damnation (Borderless),Damnation,Special Guests,68,SPG,Normal,Near Mint,English,Mythic,575098,8162164

Output JSON Format:
    [
      {
        "name": "Damnation",
        "set": "Special Guests",
        "set_code": "SPG",
        "card_number": "68",
        "rarity": "Mythic",
        "printing": "Borderless"
      }
    ]

Note: No condition/grade information is included in the JSON output.
The script automatically detects the CSV format and extracts relevant information.
"""

import csv
import json
import sys
import os
from typing import List, Dict, Optional

# No condition/grade information is used in the conversion process



def clean_card_name(name: str) -> str:
    """
    Cleans and normalizes card names.
    
    Args:
        name: Raw card name from CSV
        
    Returns:
        Cleaned card name
    """
    return name.strip()

def clean_set_name(set_name: str) -> str:
    """
    Cleans and normalizes set names.
    
    Args:
        set_name: Raw set name from CSV
        
    Returns:
        Cleaned set name
    """
    return set_name.strip() if set_name else ""

def extract_printing_info(full_name: str, simple_name: str) -> str:
    """
    Extracts printing information from the full card name.
    
    Args:
        full_name: Full card name (e.g., "Damnation (Borderless)")
        simple_name: Simple card name (e.g., "Damnation")
        
    Returns:
        Printing information or empty string
    """
    if not full_name or not simple_name:
        return ""
    
    # Remove the simple name from the full name to get printing info
    printing = full_name.replace(simple_name, "").strip()
    
    # Clean up common patterns
    printing = printing.strip("()").strip()
    
    return printing if printing else ""

def detect_csv_format(fieldnames: List[str]) -> str:
    """
    Detects the CSV format based on column headers.
    
    Args:
        fieldnames: List of column names from CSV
        
    Returns:
        Format type: "simple" or "tcgplayer"
    """
    if not fieldnames:
        return "simple"
    
    # Check for TCGplayer format indicators
    tcgplayer_indicators = {"Quantity", "Simple Name", "Card Number", "Set Code", "Product ID", "SKU"}
    if any(indicator in fieldnames for indicator in tcgplayer_indicators):
        return "tcgplayer"
    
    return "simple"

def parse_csv_file(csv_file_path: str) -> List[Dict[str, str]]:
    """
    Parses a CSV file and converts it to the required JSON format.
    
    Args:
        csv_file_path: Path to the input CSV file
        
    Returns:
        List of dictionaries with card information
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid or contains invalid data
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    products = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Try to detect the delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            # Test common delimiters
            delimiters = [',', ';', '\t']
            detected_delimiter = ','
            
            for delimiter in delimiters:
                if delimiter in sample:
                    detected_delimiter = delimiter
                    break
            
            reader = csv.DictReader(csvfile, delimiter=detected_delimiter)
            fieldnames = reader.fieldnames or []
            
            # Detect CSV format
            csv_format = detect_csv_format(fieldnames)
            print(f"📋 Detected CSV format: {csv_format}")
            
            if csv_format == "tcgplayer":
                products = parse_tcgplayer_format(reader)
            else:
                products = parse_simple_format(reader)
                    
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")
    
    return products

def parse_simple_format(reader) -> List[Dict[str, str]]:
    """
    Parses simple CSV format (name, set).
    """
    products = []
    required_columns = {"name"}
    
    # Validate that required columns exist
    if not required_columns.issubset(set(reader.fieldnames or [])):
        missing_cols = required_columns - set(reader.fieldnames or [])
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check if set column exists
    has_set_column = "set" in (reader.fieldnames or [])
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
        try:
            # Clean and validate the data
            card_name = clean_card_name(row.get('name', ''))
            
            if not card_name:
                print(f"⚠️  Warning: Skipping row {row_num} - empty card name")
                continue
            
            # Build product dictionary
            product = {
                "name": card_name
            }
            
            # Add set information if available
            if has_set_column:
                set_name = clean_set_name(row.get('set', ''))
                if set_name:
                    product["set"] = set_name
            
            products.append(product)
            
        except ValueError as e:
            print(f"❌ Error in row {row_num}: {e}")
            continue
    
    return products

def parse_tcgplayer_format(reader) -> List[Dict[str, str]]:
    """
    Parses TCGplayer CSV format.
    """
    products = []
    required_columns = {"Name", "Simple Name"}
    
    # Validate that required columns exist
    if not required_columns.issubset(set(reader.fieldnames or [])):
        missing_cols = required_columns - set(reader.fieldnames or [])
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
        try:
            # Extract and clean data
            full_name = row.get('Name', '').strip()
            simple_name = row.get('Simple Name', '').strip()
            set_name = row.get('Set', '').strip()
            set_code = row.get('Set Code', '').strip()
            card_number = row.get('Card Number', '').strip()
            rarity = row.get('Rarity', '').strip()
            
            # Use simple name as the card name
            card_name = simple_name if simple_name else full_name
            
            if not card_name:
                print(f"⚠️  Warning: Skipping row {row_num} - empty card name")
                continue
            
            # Extract printing information
            printing = extract_printing_info(full_name, simple_name)
            
            # Build product dictionary
            product = {
                "name": card_name
            }
            
            # Add optional information if available
            if set_name:
                product["set"] = set_name
            if set_code:
                product["set_code"] = set_code
            if card_number:
                product["card_number"] = card_number
            if rarity:
                product["rarity"] = rarity
            if printing:
                product["printing"] = printing
            
            products.append(product)
            
        except Exception as e:
            print(f"❌ Error in row {row_num}: {e}")
            continue
    
    return products

def save_json_file(products: List[Dict[str, str]], output_file_path: str) -> None:
    """
    Saves the products list to a JSON file.
    
    Args:
        products: List of product dictionaries
        output_file_path: Path to save the JSON file
    """
    with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(products, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully saved {len(products)} products to: {output_file_path}")

def print_usage():
    """Prints usage instructions."""
    print("""
CSV to JSON Converter for eBay MTG Card Lister
===============================================

This script converts CSV files to JSON format for eBay listing.
No condition/grade information is included in the output.

The script uses interactive prompts to get file paths.
Simply run: python csv_to_json_converter.py
    """)

def main():
    """Main function to handle user input and execute the conversion."""
    print("=" * 60)
    print("CSV to JSON Converter for eBay MTG Card Lister")
    print("=" * 60)
    print()
    
    # Get input file path from user
    while True:
        input_csv = input("📁 Enter the path to your CSV file: ").strip().strip('"')
        
        if not input_csv:
            print("❌ Please enter a valid file path.")
            continue
            
        if input_csv.lower() in ['exit', 'quit', 'q']:
            print("👋 Goodbye!")
            return
            
        if not os.path.exists(input_csv):
            print(f"❌ File not found: {input_csv}")
            print("   Please check the path and try again.")
            continue
            
        break
    
    # Get output file path from user (optional)
    output_json = input("📄 Enter output JSON file name (or press Enter for 'products.json'): ").strip().strip('"')
    if not output_json:
        output_json = "products.json"
    
    print()
    print(f"🔄 Converting CSV file: {input_csv}")
    print(f"📄 Output JSON file: {output_json}")
    print("-" * 50)
    
    try:
        # Parse the CSV file
        products = parse_csv_file(input_csv)
        
        if not products:
            print("❌ No valid products found in the CSV file.")
            return
        
        # Save to JSON
        save_json_file(products, output_json)
        
        print(f"\n📊 Summary:")
        print(f"   - Processed {len(products)} products")
        print(f"   - Output saved to: {output_json}")
        print(f"\n✅ SUCCESSFULLY CONVERTED!")
        print(f"   You can now use '{output_json}' with your eBay lister script.")
        
    except FileNotFoundError as e:
        print(f"❌ File error: {e}")
        print("   Please check the file path and try again.")
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        print("   Please check your CSV format and try again.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Please try again or check your file format.")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main() 