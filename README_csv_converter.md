# CSV to JSON Converter for eBay MTG Card Lister

## Overview
`csv_to_json_converter.py` is a specialized data conversion tool designed to transform CSV files containing Magic: The Gathering card information into JSON format compatible with the eBay MTG Card Lister script. This tool streamlines the process of preparing card inventory data for automated eBay listing.

## Features

### 🔄 Multi-Format Support
- **Simple Format**: Basic name and set information
- **TCGplayer Format**: Full TCGplayer export compatibility
- **Automatic Detection**: Automatically detects CSV format based on headers
- **Flexible Delimiters**: Supports comma, semicolon, and tab-separated files

### 📊 Data Processing
- **Card Name Cleaning**: Normalizes and validates card names
- **Set Information**: Extracts and processes set names and codes
- **Printing Information**: Handles special printings and variants
- **Rarity Data**: Preserves rarity information when available
- **Error Handling**: Robust error handling with detailed feedback

## Supported CSV Formats

### 1. Simple Format
```csv
name,set
Sol Ring,Commander 2013
Lightning Bolt,Core Set 2021
Counterspell,Dominaria
```

### 2. TCGplayer Format
```csv
Quantity,Name,Simple Name,Set,Card Number,Set Code,Printing,Condition,Language,Rarity,Product ID,SKU
1,Damnation (Borderless),Damnation,Special Guests,68,SPG,Normal,Near Mint,English,Mythic,575098,8162164
2,Lightning Bolt (Showcase),Lightning Bolt,Core Set 2021,139,M21,Showcase,Near Mint,English,Common,123456,7890123
```

## Installation

### Prerequisites
```bash
pip install csv
```

### Dependencies
- Python 3.6+
- Standard library modules (csv, json, os, sys)

## Usage

### Basic Usage
```bash
python csv_to_json_converter.py
```

### Interactive Mode
The script runs in interactive mode, prompting for:
1. **Input CSV File Path**: Path to your CSV file
2. **Output JSON File Name**: Name for the output file (defaults to `products.json`)

### Example Session
```
============================================================
CSV to JSON Converter for eBay MTG Card Lister
============================================================

📁 Enter the path to your CSV file: C:/inventory/cards.csv
📄 Enter output JSON file name (or press Enter for 'products.json'): my_products.json

🔄 Converting CSV file: C:/inventory/cards.csv
📄 Output JSON file: my_products.json
--------------------------------------------------
📋 Detected CSV format: tcgplayer
✅ Successfully saved 150 products to: my_products.json

📊 Summary:
   - Processed 150 products
   - Output saved to: my_products.json

✅ SUCCESSFULLY CONVERTED!
   You can now use 'my_products.json' with your eBay lister script.
```

## Output Format

### JSON Structure
The converter produces a JSON file with the following structure:

```json
[
  {
    "name": "Damnation",
    "set": "Special Guests",
    "set_code": "SPG",
    "card_number": "68",
    "rarity": "Mythic",
    "printing": "Borderless"
  },
  {
    "name": "Lightning Bolt",
    "set": "Core Set 2021",
    "set_code": "M21",
    "card_number": "139",
    "rarity": "Common",
    "printing": "Showcase"
  }
]
```

### Field Descriptions
- **name**: Cleaned card name (required)
- **set**: Set name (optional)
- **set_code**: Set abbreviation (optional)
- **card_number**: Collector number (optional)
- **rarity**: Card rarity (optional)
- **printing**: Special printing information (optional)

## Data Processing Details

### Card Name Cleaning
- Removes leading/trailing whitespace
- Normalizes formatting
- Validates non-empty names

### Set Name Processing
- Cleans set names of extra whitespace
- Preserves original set names
- Handles missing set information gracefully

### Printing Information Extraction
- Extracts printing variants from full card names
- Handles formats like "(Borderless)", "(Showcase)", "(Extended Art)"
- Removes printing info from base card names

### Error Handling
- **Missing Required Fields**: Skips rows with missing card names
- **Invalid Data**: Continues processing with warning messages
- **File Errors**: Provides clear error messages for file issues

## Advanced Features

### Automatic Format Detection
The script automatically detects CSV format based on column headers:

#### TCGplayer Detection
Looks for TCGplayer-specific columns:
- `Quantity`
- `Simple Name`
- `Card Number`
- `Set Code`
- `Product ID`
- `SKU`

#### Simple Format Detection
Falls back to simple format if TCGplayer indicators aren't found.

### Delimiter Detection
Automatically detects common CSV delimiters:
- Comma (`,`)
- Semicolon (`;`)
- Tab (`\t`)

### Data Validation
- Validates required fields are present
- Checks for empty or invalid card names
- Ensures data integrity before conversion

## Integration

### With eBay MTG Card Lister
The converted JSON file is directly compatible with `EbayMTGCardLister.py`:

1. **Convert CSV**: Run this converter on your inventory CSV
2. **Review Output**: Check the generated JSON file
3. **List on eBay**: Use the JSON file with the eBay lister script

### With Other Tools
The JSON output can be used with:
- Inventory management systems
- Price tracking tools
- Card database applications
- E-commerce platforms

## Error Messages and Solutions

### Common Issues

#### "File not found"
- **Solution**: Check the file path and ensure the CSV file exists
- **Tip**: Use absolute paths or ensure the file is in the same directory

#### "Missing required columns"
- **Solution**: Ensure your CSV has a "name" column (or "Name" for TCGplayer format)
- **Tip**: Check CSV headers match expected format

#### "CSV parsing error"
- **Solution**: Verify CSV file is properly formatted
- **Tip**: Open in a text editor to check for encoding issues

#### "No valid products found"
- **Solution**: Check that CSV contains valid card data
- **Tip**: Ensure card names are not empty

## Best Practices

### CSV Preparation
1. **Use Standard Formats**: Follow TCGplayer export format when possible
2. **Clean Data**: Remove extra spaces and formatting before conversion
3. **Validate Names**: Ensure card names match official MTG card names
4. **Include Set Info**: Add set information for better eBay listings

### File Management
1. **Backup Originals**: Keep original CSV files as backup
2. **Test Conversion**: Test with small files before processing large inventories
3. **Review Output**: Always review converted JSON before using with eBay lister

### Data Quality
1. **Consistent Formatting**: Use consistent naming conventions
2. **Complete Information**: Include as much card information as possible
3. **Regular Updates**: Keep inventory data current and accurate

## Troubleshooting

### Performance Issues
- **Large Files**: Process large CSV files in smaller batches
- **Memory Usage**: Close other applications when processing large files
- **Processing Time**: Allow adequate time for large file conversion

### Data Issues
- **Encoding Problems**: Ensure CSV files use UTF-8 encoding
- **Special Characters**: Handle special characters in card names properly
- **Missing Data**: Use placeholder values for missing optional fields

## Future Enhancements

### Planned Features
1. **Batch Processing**: Support for multiple CSV files
2. **Custom Formats**: User-defined CSV format templates
3. **Data Validation**: Enhanced validation with MTG card database
4. **Price Integration**: Automatic price lookup during conversion
5. **Image URLs**: Integration with card image databases
6. **Condition Mapping**: Automatic condition grade conversion

### API Integration
- **Scryfall API**: Real-time card data validation
- **TCGplayer API**: Direct data import
- **eBay API**: Direct listing creation

## Support

For technical support:
1. Check error messages for specific guidance
2. Verify CSV format matches supported formats
3. Test with sample data first
4. Ensure all dependencies are installed

## License

This tool is designed for Magic: The Gathering card shop automation and inventory management. 