import json
import requests
import os

# Temporarily hardcode the token for testing
EBAY_OAUTH_TOKEN = "v^1.1#i^1#I^3#f^0#p^3#r^1#t^Ul4xMF8xOkU2NjUyMjNDRURGNzI2RDEzNjA5MkNFRkRFNTY3MjY3XzFfMSNFXjEyODQ="

EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "sandbox")

# Check if token is available
if not EBAY_OAUTH_TOKEN:
    print("❌ Error: EBAY_OAUTH_TOKEN not available!")
    exit(1)

if EBAY_ENVIRONMENT == "production":
    BASE_URL = "https://api.ebay.com"
else:
    BASE_URL = "https://api.sandbox.ebay.com"

HEADERS = {
    "Authorization": f"Bearer {EBAY_OAUTH_TOKEN}",
    "Content-Type": "application/json",
    "Content-Language": "en-US"
}

def test_simple_upload():
    """Test with absolutely minimal data"""
    sku = "TEST-SIMPLE-001"
    url = f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}"
    
    # Minimal payload - no aspects at all
    payload = {
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "condition": "NEW",
        "product": {
            "title": "Test Magic Card - Simple",
            "description": "Simple test description for Magic card",
            "imageUrls": ["https://cards.scryfall.io/large/front/j/a/jace-the-perfected-mind.jpg"]
        }
    }
    
    print("Testing minimal upload...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201, 204]:
            print("✅ Minimal upload successful!")
            return True
        else:
            print("❌ Minimal upload failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_aspects():
    """Test with properly formatted aspects"""
    sku = "TEST-ASPECTS-001"
    url = f"{BASE_URL}/sell/inventory/v1/inventory_item/{sku}"
    
    # Test with underscores instead of spaces
    payload = {
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "condition": "NEW",
        "product": {
            "title": "Test Magic Card - With Aspects",
            "description": "Test with aspects for Magic card",
            "imageUrls": ["https://cards.scryfall.io/large/front/j/a/jace-the-perfected-mind.jpg"],
            "aspects": {
                "Game": ["Magic: The Gathering"],
                "Card_Type": ["Planeswalker"],
                "Rarity": ["Mythic Rare"],
                "Language": ["English"]
            }
        }
    }
    
    print("\nTesting with aspects...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.put(url, headers=HEADERS, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201, 204]:
            print("✅ Aspects upload successful!")
            return True
        else:
            print("❌ Aspects upload failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing eBay API with minimal data...\n")
    
    # Test 1: Minimal upload
    success1 = test_simple_upload()
    
    # Test 2: With aspects
    success2 = test_with_aspects()
    
    print(f"\n📊 Results:")
    print(f"Minimal upload: {'✅' if success1 else '❌'}")
    print(f"With aspects: {'✅' if success2 else '❌'}")