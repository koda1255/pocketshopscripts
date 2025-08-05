

import json
import requests
import os
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime

# --- Configuration ---
# Load sensitive data from environment variables for security.
EBAY_OAUTH_TOKEN = os.getenv("EBAY_OAUTH_TOKEN", "v^1.1#i^1#I^3#p^3#r^0#f^0#t^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")
EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "production")  # "production" or "sandbox"
EBAY_MERCHANT_LOCATION = os.getenv("EBAY_MERCHANT_LOCATION", "Montgomery_TX_01") # e.g., "MyWarehouse"
EBAY_FULFILLMENT_POLICY_ID = os.getenv("EBAY_FULFILLMENT_POLICY_ID", "256353666016")
EBAY_PAYMENT_POLICY_ID = os.getenv("EBAY_PAYMENT_POLICY_ID", "256353588016")
EBAY_RETURN_POLICY_ID = os.getenv("EBAY_RETURN_POLICY_ID", "256353613016")


#
# eBay MTG Card Lister Script
#
# Description:
# This script automates listing Magic: The Gathering cards on eBay using the Inventory API.
# It follows the standard three-step process:
#   1. Create or Update an Inventory Item (the product's details).
#   2. Create an Offer (the listing's price, policies, and quantity).
#   3. Publish the Offer (makes the listing live on eBay).
#
# The script reads card information from a `products.json` file, fetches detailed data
# and pricing from the Scryfall API, and then lists each card on eBay.
#
# --- SETUP ---
#
# 1. Install Dependencies:
#    pip install requests
#
# 2. Set Environment Variables:
#    For security, your eBay API credentials and policy IDs should be set as
#    environment variables, not hardcoded in the script.
#
#    - EBAY_OAUTH_TOKEN: Your OAuth access token.
#    - EBAY_MERCHANT_LOCATION_KEY: The key for your inventory location (e.g., "MyWarehouse").
#    - EBAY_FULFILLMENT_POLICY_ID: The ID for your shipping policy.
#    - EBAY_PAYMENT_POLICY_ID: The ID for your payment policy.
#    - EBAY_RETURN_POLICY_ID: The ID for your return policy.
#
# 3. Create `products.json`:
#    In the same directory as the script, create a file named `products.json`.
#    This file contains a list of the cards you want to sell.
#
#    Example `products.json`:
#    [
#      {
#        "name": "Sol Ring",
#        "grade": "NM"
#      },
#      {
#        "name": "Lightning Bolt",
#        "grade": "EX"
#      },
#      {
#        "name": "Counterspell",
#        "grade": "VG"
#      }
#    ]
#
#    Accepted Grades: "NM" (Near Mint), "EX" (Excellent), "VG" (Very Good), "P" (Poor)
#
# --- USAGE ---
#
#    Run the script from your terminal:
#    python ebay_lister_script.py
#



# Determine API endpoint based on environment (production or sandbox)
EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "production")
BASE_URL = "https://api.ebay.com" if EBAY_ENVIRONMENT == "production" else "https://api.sandbox.ebay.com"

# Standard headers for all API requests
HEADERS = {
    "Authorization": f"Bearer {EBAY_OAUTH_TOKEN}",
    "Content-Type": "application/json",
    "Content-Language": "en-US"
}

# --- Mappings for Magic: The Gathering Card Conditions ---
# Maps your grade ("NM", "EX", etc.) to eBay's required `condition` enum.
# For Trading Cards, eBay requires 'LIKE_NEW' for graded and 'USED_VERY_GOOD' for ungraded cards.
EBAY_CONDITION_ENUM_MAP = {
    "NM": "LIKE_NEW",         # Graded (Near Mint)
    "EX": "USED_VERY_GOOD",   # Ungraded (Excellent/Lightly Played)
    "VG": "USED_VERY_GOOD",   # Ungraded (Very Good/Moderately Played)
    "P":  "USED_VERY_GOOD",   # Ungraded (Poor/Heavily Played)
}

# Maps your grade to eBay's specific "Card Condition" item specific value ID.
# This is required for the Trading Card category.
EBAY_CARD_CONDITION_VALUES = {
    "NM": "400010",  # Near Mint or Better
    "EX": "400015",  # Lightly Played (Excellent)
    "VG": "400016",  # Moderately Played (Very Good)
    "P":  "400017",  # Heavily Played (Poor)
}

# Map for Card Condition descriptor name (numeric ID for category 183454)
EBAY_CARD_CONDITION_DESCRIPTOR_ID = "40001"  # Correct for trading cards (CCG Individual Cards)

def get_condition_description(condition_grade: str) -> str:
    """Generates a detailed condition description based on a grade."""
    descriptions = {
        "NM": "Near Mint (NM): Minimal to no wear from shuffling, play or handling.",
        "EX": "Excellent (EX) / Lightly Played (LP): Minor border or corner wear, or slight scuffs or scratches.",
        "VG": "Very Good (VG) / Moderately Played (MP): Moderate border wear, corner wear, scratching or scuffing.",
        "P": "Poor (P) / Heavily Played (HP): Major whitening, corner wear, scratching, and/or creases.",
    }
    return descriptions.get(condition_grade, "Card condition as per description and photos.")

# --- Data Preparation Functions ---

def fetch_scryfall_data(card_name: str, set_code: str = None, card_number: str = None) -> Optional[Dict]:
    """Fetches card data from the Scryfall API."""
    try:
        if set_code and card_number:
            # Try to find the specific card in the specified set using collector number
            url = f"https://api.scryfall.com/cards/{set_code}/{card_number}"
            print(f"🔍 Fetching Scryfall data for: {card_name} in set {set_code} (number {card_number})")
        elif set_code:
            # Try to find the specific card in the specified set
            url = f"https://api.scryfall.com/cards/{set_code}/{card_name}"
            print(f"🔍 Fetching Scryfall data for: {card_name} in set {set_code}")
        else:
            # Fallback to general search
            url = f"https://api.scryfall.com/cards/named?exact={requests.utils.quote(card_name)}"
            print(f"🔍 Fetching Scryfall data for: {card_name}")
        
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        card_data = response.json()
        print(f"✅ Found data for '{card_data['name']}' from set '{card_data['set_name']}'")
        return card_data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from Scryfall for '{card_name}': {e}")
        return None

def generate_sku(card_name: str, set_code: str, collector_number: str, grade: str) -> str:
    """Generates a unique SKU for the card."""
    clean_name = ''.join(c for c in card_name if c.isalnum()).upper()
    return f"MTG-{set_code.upper()}-{collector_number}-{grade}-{str(uuid.uuid4())[:4]}"

def build_inventory_item_payload(scryfall_data: Dict, grade: str, sku: str) -> Dict:
    """Builds the dictionary for the 'inventory_item' API call."""
    image_url = scryfall_data.get('image_uris', {}).get('normal')
    description = (
        f"🎴 {scryfall_data['name']} - {scryfall_data.get('set_name', 'Magic: The Gathering')}\n\n"
        f"Set: {scryfall_data.get('set_name', 'Unknown Set')} ({scryfall_data.get('set', '').upper()})\n"
        f"Collector Number: {scryfall_data.get('collector_number', '')}\n"
        f"Rarity: {scryfall_data.get('rarity', 'Unknown').title()}\n\n"
        f"Condition: {get_condition_description(grade)}\n\n"
        "All cards are 100% authentic Magic: The Gathering cards. Shipped with care."
    )

    item_condition = EBAY_CONDITION_ENUM_MAP.get(grade, "USED_VERY_GOOD")
    ebay_card_condition_value = EBAY_CARD_CONDITION_VALUES.get(grade, "400015") # Default to Excellent

    item_payload = {
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "condition": item_condition,
        "conditionDescriptors": [{
            "name": EBAY_CARD_CONDITION_DESCRIPTOR_ID,  # Use numeric ID, not string
            "values": [ebay_card_condition_value]
        }],
        "packageWeightAndSize": {
            "weight": {
                "value": 1,
                "unit": "OUNCE"
            }
        },
        "product": {
            "title": f"MTG - {scryfall_data['name']} - {scryfall_data.get('set_name')} - {grade}",
            "description": description,
            "aspects": {
                "Game": ["Magic: The Gathering"],
                "Card Name": [scryfall_data['name']],
                "Set": [scryfall_data.get('set_name', 'Unknown')],
                "Rarity": [scryfall_data.get('rarity', 'Unknown')],
                "Graded": ["No"],
            },
            "imageUrls": [image_url] if image_url else []
        }
    }
    if grade != "NM":
        item_payload["conditionDescription"] = get_condition_description(grade)
    return item_payload

def build_offer_payload(sku: str, scryfall_data: Dict, grade: str) -> Dict:
    """Builds the dictionary for the 'createOffer' API call."""
    try:
        price_str = scryfall_data.get('prices', {}).get('usd', '1.00')
        price = float(price_str) if price_str else 1.00
    except (ValueError, TypeError):
        price = 1.00
    
    list_price = f"{price:.2f}"

    offer_payload = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "availableQuantity": 1,
        "categoryId": "183454",  # eBay Category ID for MTG Individual Cards
        "listingDescription": f"See item description for full details on {scryfall_data['name']}.",
        "listingPolicies": {
            "fulfillmentPolicyId": EBAY_FULFILLMENT_POLICY_ID,
            "paymentPolicyId": EBAY_PAYMENT_POLICY_ID,
            "returnPolicyId": EBAY_RETURN_POLICY_ID,
        },
        "merchantLocationKey": EBAY_MERCHANT_LOCATION,
        "pricingSummary": {
            "price": {
                "value": list_price,
                "currency": "USD"
            }
        }
    }
    return offer_payload

# --- eBay API Functions ---

def create_or_update_inventory_item(sku: str, payload: Dict) -> bool:
    """
    STEP 1: Creates or updates an inventory item on eBay.
    This corresponds to: POST /sell/inventory/v1/inventory_item/{SKU}
    (Note: The API uses PUT for create/update, which is what this function does).
    """
    url = f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}"
    print(f"  [Step 1] Uploading inventory item for SKU: {sku}...")
    print(f"  [Step 1] Inventory payload: {json.dumps(payload, indent=2)}")
    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        print(f"  [Step 1] Response status: {response.status_code}")
        print(f"  [Step 1] Response body: {response.text}")
        if response.status_code in [200, 201, 204]:
            print(f"  ✅ [Step 1] Success: Inventory item created/updated.")
            return True
        else:
            print(f"  ❌ [Step 1] Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ [Step 1] An exception occurred: {e}")
        return False

def create_offer(payload: Dict) -> Optional[str]:
    """
    STEP 2: Creates an offer for a given SKU.
    This corresponds to: POST /sell/inventory/v1/offer
    Includes a retry mechanism to handle eBay's inventory processing delay.
    """
    sku = payload["sku"]
    url = f"{BASE_URL}/sell/inventory/v1/offer"
    max_attempts = 3
    print(f"  [Step 2] Offer payload: {json.dumps(payload, indent=2)}")
    for attempt in range(max_attempts):
        wait_time = 10 + (attempt * 5)
        print(f"  [Step 2] Waiting {wait_time}s before creating offer (Attempt {attempt + 1}/{max_attempts})...")
        time.sleep(wait_time)
        print(f"  [Step 2] Creating offer for SKU: {sku}...")
        try:
            response = requests.post(url, headers=HEADERS, json=payload)
            print(f"  [Step 2] Response status: {response.status_code}")
            print(f"  [Step 2] Response body: {response.text}")
            if response.status_code == 201:
                offer_id = response.json().get("offerId")
                print(f"  ✅ [Step 2] Success: Created Offer ID: {offer_id}")
                return offer_id
            else:
                response_text = response.text
                print(f"  ❌ [Step 2] Offer creation failed on attempt {attempt + 1}: {response.status_code} - {response_text}")
                if "SKU could not be found" not in response_text:
                    break
        except Exception as e:
            print(f"  ❌ [Step 2] An exception occurred: {e}")
            break
    return None

def publish_offer(offer_id: str) -> Optional[str]:
    """
    STEP 3: Publishes a specific offer to make it a live listing.
    This corresponds to: POST /sell/inventory/v1/offer/{offerId}/publish
    """
    url = f"{BASE_URL}/sell/inventory/v1/offer/{offer_id}/publish"
    print(f"  [Step 3] Publishing Offer ID: {offer_id}...")
    try:
        response = requests.post(url, headers=HEADERS)
        print(f"  [Step 3] Response status: {response.status_code}")
        print(f"  [Step 3] Response body: {response.text}")
        if response.status_code == 200:
            listing_id = response.json().get("listingId")
            print(f"  ✅ [Step 3] Success! 🎉 Live Listing ID: {listing_id}")
            return listing_id
        else:
            print(f"  ❌ [Step 3] Failed to publish: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ [Step 3] An exception occurred: {e}")
        return None

# --- Main Execution ---

def main():
    """Main function to drive the listing process."""
    if not all([EBAY_OAUTH_TOKEN, EBAY_MERCHANT_LOCATION, EBAY_FULFILLMENT_POLICY_ID, EBAY_PAYMENT_POLICY_ID, EBAY_RETURN_POLICY_ID]):
        print("❌ Critical Error: One or more required environment variables are missing.")
        print("   Please set: EBAY_OAUTH_TOKEN, EBAY_MERCHANT_LOCATION_KEY, EBAY_FULFILLMENT_POLICY_ID, EBAY_PAYMENT_POLICY_ID, EBAY_RETURN_POLICY_ID")
        return

    try:
        with open("products.json", "r") as f:
            products_to_list = json.load(f)
    except FileNotFoundError:
        print("❌ Error: `products.json` not found. Please create it and add products to list.")
        return
    except json.JSONDecodeError:
        print("❌ Error: `products.json` contains invalid JSON. Please check the file format.")
        return

    print(f"📦 Found {len(products_to_list)} products to process from `products.json`...")
    successful_listings = 0
    
    for i, product_info in enumerate(products_to_list):
        card_name = product_info.get("name")
        grade = product_info.get("grade", "EX").upper()
        
        print(f"\n--- Processing Item {i+1}/{len(products_to_list)}: {card_name} ({grade}) ---")

        if not card_name:
            print("⚠️ Skipping item with no name.")
            continue

        # Prepare Data - Use set information if available
        set_code = product_info.get("set_code")
        card_number = product_info.get("card_number")
        scryfall_data = fetch_scryfall_data(card_name, set_code, card_number)
        if not scryfall_data:
            print(f"Skipping '{card_name}' due to Scryfall data fetch failure.")
            continue
            
        sku = generate_sku(
            card_name,
            scryfall_data.get('set', ''),
            scryfall_data.get('collector_number', ''),
            grade
        )

        # --- Execute eBay API Flow ---
        
        # Step 1: Create Inventory Item
        inventory_payload = build_inventory_item_payload(scryfall_data, grade, sku)
        print(f"[DEBUG] Inventory payload for SKU {sku}: {json.dumps(inventory_payload, indent=2)}")
        if not create_or_update_inventory_item(sku, inventory_payload):
            print(f"Halting process for SKU {sku} after inventory item failure.")
            continue

        # Step 2: Create Offer
        offer_payload = build_offer_payload(sku, scryfall_data, grade)
        print(f"[DEBUG] Offer payload for SKU {sku}: {json.dumps(offer_payload, indent=2)}")
        offer_id = create_offer(offer_payload)
        print(f"[DEBUG] Offer ID returned: {offer_id}")
        if not offer_id:
            print(f"Halting process for SKU {sku} after offer creation failure.")
            continue

        # Step 3: Publish Offer
        print(f"[DEBUG] Publishing offer with ID: {offer_id}")
        listing_id = publish_offer(offer_id)
        if listing_id:
            successful_listings += 1

    print("\n--- Listing Process Complete ---")
    print(f"📊 Summary: Successfully published {successful_listings} out of {len(products_to_list)} items.")

if __name__ == "__main__":
    main()
