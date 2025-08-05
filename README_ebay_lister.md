# eBay MTG Card Lister

## Overview
`EbayMTGCardLister.py` is a comprehensive automation tool for listing Magic: The Gathering cards on eBay using the eBay Inventory API. This script streamlines the entire process from card data preparation to live eBay listings, making it an essential tool for MTG card shop owners and sellers.

## Features

### 🚀 Automated Listing Process
- **Three-Step Workflow**: Inventory Item → Offer → Publish
- **Batch Processing**: Process multiple cards from a single JSON file
- **Automatic Data Fetching**: Retrieves card details from Scryfall API
- **Condition Mapping**: Converts card grades to eBay condition standards
- **SKU Generation**: Creates unique SKUs for inventory management

### 📊 Data Integration
- **Scryfall API Integration**: Fetches comprehensive card data and pricing
- **JSON Input**: Processes card data from `products.json` file
- **Condition Support**: Handles NM, EX, VG, and P card conditions
- **Set Information**: Supports specific set and collector number matching

### 🛡️ Error Handling & Reliability
- **Retry Mechanisms**: Handles eBay API processing delays
- **Comprehensive Logging**: Detailed success/failure reporting
- **Graceful Degradation**: Continues processing even if individual cards fail
- **Validation**: Ensures all required data is present before listing

## Prerequisites

### eBay API Setup
1. **eBay Developer Account**: Create an account at [eBay Developers](https://developer.ebay.com/)
2. **Application Creation**: Create a new application in the eBay developer portal
3. **OAuth Token**: Generate an OAuth access token for API authentication
4. **Policy IDs**: Set up fulfillment, payment, and return policies

### Required Dependencies
```bash
pip install requests
```

### Environment Variables
Set the following environment variables for security:

```bash
# Required
EBAY_OAUTH_TOKEN=your_oauth_token_here
EBAY_MERCHANT_LOCATION=your_merchant_location_key
EBAY_FULFILLMENT_POLICY_ID=your_fulfillment_policy_id
EBAY_PAYMENT_POLICY_ID=your_payment_policy_id
EBAY_RETURN_POLICY_ID=your_return_policy_id

# Optional
EBAY_ENVIRONMENT=production  # or "sandbox" for testing
```

## Installation & Setup

### 1. Environment Configuration
Create a `.env` file or set environment variables:

```bash
# Windows (PowerShell)
$env:EBAY_OAUTH_TOKEN="your_token_here"
$env:EBAY_MERCHANT_LOCATION="Montgomery_TX_01"
$env:EBAY_FULFILLMENT_POLICY_ID="256353666016"
$env:EBAY_PAYMENT_POLICY_ID="256353588016"
$env:EBAY_RETURN_POLICY_ID="256353613016"

# Linux/Mac
export EBAY_OAUTH_TOKEN="your_token_here"
export EBAY_MERCHANT_LOCATION="Montgomery_TX_01"
export EBAY_FULFILLMENT_POLICY_ID="256353666016"
export EBAY_PAYMENT_POLICY_ID="256353588016"
export EBAY_RETURN_POLICY_ID="256353613016"
```

### 2. Input File Preparation
Create a `products.json` file with your card inventory:

```json
[
  {
    "name": "Sol Ring",
    "grade": "NM",
    "set_code": "C13",
    "card_number": "215"
  },
  {
    "name": "Lightning Bolt",
    "grade": "EX",
    "set_code": "M21",
    "card_number": "139"
  },
  {
    "name": "Counterspell",
    "grade": "VG"
  }
]
```

### 3. Card Condition Grades
Supported condition grades and their eBay mappings:

| Grade | eBay Condition | Card Condition Value | Description |
|-------|----------------|---------------------|-------------|
| NM | LIKE_NEW | 400010 | Near Mint or Better |
| EX | USED_VERY_GOOD | 400015 | Lightly Played (Excellent) |
| VG | USED_VERY_GOOD | 400016 | Moderately Played (Very Good) |
| P | USED_VERY_GOOD | 400017 | Heavily Played (Poor) |

## Usage

### Basic Usage
```bash
python EbayMTGCardLister.py
```

### Execution Flow
The script follows a three-step process for each card:

#### Step 1: Create/Update Inventory Item
- Fetches card data from Scryfall API
- Builds comprehensive item description
- Sets condition and item specifics
- Uploads to eBay inventory system

#### Step 2: Create Offer
- Generates pricing from Scryfall data
- Sets listing policies and location
- Creates offer with inventory item
- Handles eBay processing delays

#### Step 3: Publish Offer
- Publishes offer to create live listing
- Returns eBay listing ID
- Confirms successful publication

### Example Output
```
--- Processing Item 1/3: Sol Ring (NM) ---
🔍 Fetching Scryfall data for: Sol Ring in set C13 (number 215)
✅ Found data for 'Sol Ring' from set 'Commander 2013'
  [Step 1] Uploading inventory item for SKU: MTG-C13-215-NM-a1b2...
  ✅ [Step 1] Success: Inventory item created/updated.
  [Step 2] Creating offer for SKU: MTG-C13-215-NM-a1b2...
  ✅ [Step 2] Success: Created Offer ID: 123456789
  [Step 3] Publishing Offer ID: 123456789...
  ✅ [Step 3] Success! 🎉 Live Listing ID: 987654321

--- Processing Item 2/3: Lightning Bolt (EX) ---
...
```

## Configuration Options

### API Endpoints
```python
# Production vs Sandbox
EBAY_ENVIRONMENT = "production"  # or "sandbox"
BASE_URL = "https://api.ebay.com" if EBAY_ENVIRONMENT == "production" else "https://api.sandbox.ebay.com"
```

### Retry Settings
```python
# Offer creation retry mechanism
max_attempts = 3
wait_time = 10 + (attempt * 5)  # Progressive delay: 10s, 15s, 20s
```

### Category Settings
```python
# eBay Category ID for MTG Individual Cards
categoryId = "183454"
```

## Advanced Features

### Scryfall Integration
- **Automatic Data Fetching**: Retrieves card details, images, and pricing
- **Set-Specific Lookup**: Uses set codes and collector numbers for precise matching
- **Fallback Search**: General search if specific set data unavailable
- **Price Integration**: Uses Scryfall pricing data for listing prices

### SKU Generation
```python
# Format: MTG-{SET}-{NUMBER}-{GRADE}-{UUID}
# Example: MTG-C13-215-NM-a1b2
```

### Description Generation
Automatically creates comprehensive listings with:
- Card name and set information
- Collector number and rarity
- Condition description
- Professional formatting
- Authenticity guarantee

### Image Integration
- **Automatic Image URLs**: Includes card images from Scryfall
- **High-Quality Images**: Uses normal resolution card images
- **Image Validation**: Ensures image URLs are accessible

## Error Handling

### Common Issues & Solutions

#### Authentication Errors
```
❌ Critical Error: One or more required environment variables are missing.
```
**Solution**: Verify all environment variables are set correctly

#### Scryfall API Errors
```
❌ Error fetching data from Scryfall for 'Card Name': 404 Client Error
```
**Solution**: Check card name spelling and set information

#### eBay API Errors
```
❌ [Step 1] Failed: 400 - Invalid request
```
**Solution**: Review API payload and ensure all required fields are present

#### File Errors
```
❌ Error: `products.json` not found
```
**Solution**: Ensure `products.json` exists in the script directory

### Retry Logic
- **Automatic Retries**: Retries failed operations with progressive delays
- **Error Recovery**: Continues processing remaining cards after failures
- **Detailed Logging**: Provides comprehensive error information

## Monitoring & Logging

### Success Tracking
- **Progress Reporting**: Shows current item being processed
- **Success Count**: Tracks successfully published listings
- **Summary Report**: Final summary of processing results

### Debug Information
- **API Payloads**: Logs request payloads for debugging
- **Response Details**: Shows API response status and content
- **Timing Information**: Tracks processing time for each step

## Security Considerations

### API Token Security
- **Environment Variables**: Store sensitive data in environment variables
- **Token Rotation**: Regularly rotate OAuth tokens
- **Access Control**: Limit API access to necessary permissions

### Data Privacy
- **Local Processing**: All data processing occurs locally
- **No Data Storage**: Script doesn't store sensitive information
- **Secure Transmission**: Uses HTTPS for all API communications

## Integration

### With Other Tools
- **CSV Converter**: Use with `csv_to_json_converter.py` for CSV imports
- **Card Detection**: Integrate with `detectname.py` for automated card identification
- **Inventory Systems**: Compatible with existing inventory management

### Workflow Integration
1. **Inventory Preparation**: Use CSV converter or manual JSON creation
2. **Card Detection**: Optionally use card detection tool for inventory
3. **eBay Listing**: Run this script to create listings
4. **Monitoring**: Track listing performance and sales

## Performance Optimization

### Batch Processing
- **Efficient Processing**: Processes multiple cards in sequence
- **Memory Management**: Handles large inventories efficiently
- **Progress Tracking**: Shows real-time processing status

### API Optimization
- **Rate Limiting**: Respects eBay API rate limits
- **Efficient Requests**: Minimizes API calls through smart data fetching
- **Caching**: Avoids redundant data requests

## Troubleshooting

### Common Problems

#### "SKU could not be found"
- **Cause**: Inventory item creation failed
- **Solution**: Check API credentials and payload format

#### "Invalid category"
- **Cause**: Category ID mismatch
- **Solution**: Verify category ID is correct for MTG cards

#### "Policy not found"
- **Cause**: Policy IDs are incorrect
- **Solution**: Verify all policy IDs in environment variables

#### "Authentication failed"
- **Cause**: OAuth token expired or invalid
- **Solution**: Generate new OAuth token

### Debug Mode
Enable detailed logging by modifying the script:
```python
# Add debug logging
print(f"[DEBUG] API Response: {response.text}")
```

## Future Enhancements

### Planned Features
1. **Bulk Operations**: Support for bulk listing operations
2. **Price Optimization**: Dynamic pricing based on market conditions
3. **Image Upload**: Direct image upload to eBay
4. **Condition Assessment**: Automatic condition evaluation
5. **Market Analysis**: Integration with market data APIs
6. **Automated Relisting**: Automatic relisting of sold items

### API Improvements
1. **Webhook Support**: Real-time listing status updates
2. **Advanced Filtering**: More sophisticated card filtering options
3. **Multi-Marketplace**: Support for other marketplaces
4. **Analytics Integration**: Sales and performance tracking

## Support

### Getting Help
1. **Check Logs**: Review detailed error messages
2. **Verify Setup**: Ensure all prerequisites are met
3. **Test Environment**: Use sandbox environment for testing
4. **API Documentation**: Refer to eBay API documentation

### Best Practices
1. **Test First**: Always test with sandbox environment
2. **Backup Data**: Keep backups of your `products.json` file
3. **Monitor Listings**: Regularly check listing status
4. **Update Regularly**: Keep API tokens and policies current

## License

This tool is designed for Magic: The Gathering card shop automation and eBay listing management. 