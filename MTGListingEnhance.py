import requests
import json
import time

def fetch_card_info(card_name):
    url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "name": data["name"],
            "set": data["set_name"],
            "rarity": data["rarity"],
            "type": data["type_line"],
            "oracle": data.get("oracle_text", ""),
            "image_url": data["image_uris"]["normal"]
        }
    else:
        print(f"⚠️ Warning: Card '{card_name}' not found.")
        return None

def create_description(card):
    return (
        f"{card['name']} - {card['type']}\n"
        f"Set: {card['set']}\n"
        f"Rarity: {card['rarity']}\n\n"
        f"{card['oracle']}"
    )

def enhance_listings(input_file, output_file):
    with open(input_file, "r") as f:
        listings = json.load(f)

    updated_listings = []
    for listing in listings:
        card_name = listing.get("title") or listing.get("name")
        if not card_name:
            continue

        card_info = fetch_card_info(card_name)
        if card_info:
            listing["title"] = card_info["name"]
            listing["image_url"] = card_info["image_url"]
            listing["description"] = create_description(card_info)
            updated_listings.append(listing)

        time.sleep(0.1)  # Respect API limits

    with open(output_file, "w") as f:
        json.dump(updated_listings, f, indent=2)
    print(f"✅ Updated listings saved to {output_file}")

# Run the script
enhance_listings("mtg_listings.json", "updated_listings.json")