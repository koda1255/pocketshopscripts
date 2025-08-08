

import discord
import os
import csv
import json
import requests
import asyncio
import io

# --- Import logic from your existing scripts ---
# We will assume your other scripts can be imported.
# This might require minor adjustments to them (e.g., ensuring they don't run code automatically when imported).
from EbayMTGCardLister import main as run_ebay_lister, fetch_scryfall_data
from csv_to_json_converter import process_csv_content

# --- Configuration ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
# The channel the bot will listen for CSV uploads in.
LISTEN_CHANNEL_NAME = "datadump" 
# The channel where the bot will post results and the bulk CSV.
RESULTS_CHANNEL_NAME = "results" 
PRICE_THRESHOLD = 1.00

# --- Bot Setup ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

async def send_status(channel, message):
    """Sends a status update to the specified channel."""
    print(f"[STATUS] {message}")
    await channel.send(f":robot: {message}")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print(f"Listening for CSVs in channel: #{LISTEN_CHANNEL_NAME}")
    print(f"Posting results in channel: #{RESULTS_CHANNEL_NAME}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the message is in the correct channel and has a CSV attachment
    if message.channel.name == LISTEN_CHANNEL_NAME and message.attachments:
        attachment = message.attachments[0]
        if attachment.filename.lower().endswith('.csv'):
            # Find the results channel
            results_channel = discord.utils.get(message.guild.channels, name=RESULTS_CHANNEL_NAME)
            if not results_channel:
                await message.channel.send(f"Error: Cannot find results channel `#{RESULTS_CHANNEL_NAME}`. Please create it.")
                return

            await send_status(results_channel, f"New file detected: `{attachment.filename}`. Starting processing...")
            
            try:
                # Download CSV content
                csv_content_bytes = await attachment.read()
                csv_content_text = csv_content_bytes.decode('utf-8')
                
                # Use your existing CSV processor to get a list of card names
                # We assume process_csv_file takes the CSV text and returns a list of dicts like [{'name': 'Card Name'}, ...]
                card_list = process_csv_content(io.StringIO(csv_content_text))

                high_value_cards = []
                low_value_cards = []

                await send_status(results_channel, f"Checking prices for {len(card_list)} cards. This may take a moment...")

                # Process each card to check its price
                for i, card in enumerate(card_list):
                    card_name = card.get("name")
                    if not card_name:
                        continue

                    await send_status(results_channel, f"Checking ({i+1}/{len(card_list)}): {card_name}...")
                    
                    # Use the function from your eBay lister to get Scryfall data
                    scryfall_data = fetch_scryfall_data(card_name)
                    await asyncio.sleep(0.1) # Be kind to the Scryfall API

                    if scryfall_data:
                        price_str = scryfall_data.get('prices', {}).get('usd', '0')
                        price = float(price_str) if price_str else 0.0

                        card_info_for_output = {
                            "name": scryfall_data.get("name"),
                            "set": scryfall_data.get("set_name"),
                            "price": price,
                            "grade": card.get("grade", "NM") # Carry over grade if it exists
                        }

                        if price >= PRICE_THRESHOLD:
                            high_value_cards.append(card_info_for_output)
                        else:
                            low_value_cards.append(card_info_for_output)
                    else:
                        await send_status(results_channel, f"⚠️ Could not find price data for `{card_name}`. Skipping.")

                # --- Handle High-Value Cards ---
                if high_value_cards:
                    await send_status(results_channel, f"Found {len(high_value_cards)} cards valued at ${PRICE_THRESHOLD} or more. Creating `products.json` for eBay listing.")
                    
                    # Create the products.json file expected by the eBay lister
                    with open("products.json", "w") as f:
                        json.dump(high_value_cards, f, indent=2)
                    
                    await send_status(results_channel, "Handing off to the eBay lister script...")
                    
                    # Capture the output from the lister script to post it to Discord
                    lister_output_capture = io.StringIO()
                    import sys
                    original_stdout = sys.stdout
                    sys.stdout = lister_output_capture
                    
                    try:
                        run_ebay_lister()
                    finally:
                        sys.stdout = original_stdout # Restore stdout
                    
                    lister_output = lister_output_capture.getvalue()
                    
                    # Send the lister's output to Discord
                    await send_status(results_channel, "--- eBay Lister Output ---")
                    if len(lister_output) > 1950:
                        for chunk in [lister_output[i:i+1950] for i in range(0, len(lister_output), 1950)]:
                            await results_channel.send(f"```\n{chunk}\n```")
                    else:
                        await results_channel.send(f"```\n{lister_output}\n```")
                    await send_status(results_channel, "--- End eBay Lister Output ---")

                # --- Handle Low-Value Cards ---
                if low_value_cards:
                    await send_status(results_channel, f"Found {len(low_value_cards)} cards valued under ${PRICE_THRESHOLD}. Creating a new CSV for them.")
                    
                    # Create a new CSV file in memory
                    output_csv = io.StringIO()
                    writer = csv.writer(output_csv)
                    writer.writerow(['Name', 'Set', 'Price', 'Grade']) # Header
                    for card in low_value_cards:
                        writer.writerow([card['name'], card['set'], card['price'], card['grade']])
                    
                    output_csv.seek(0) # Rewind the file to the beginning
                    
                    # Upload the new CSV to the results channel
                    await results_channel.send(
                        content="Here is the list of low-value cards:",
                        file=discord.File(fp=io.BytesIO(output_csv.getvalue().encode()), filename="low_value_cards.csv")
                    )

                await send_status(results_channel, "✅ Processing complete.")

            except Exception as e:
                await send_status(results_channel, f"An error occurred: {e}")


def start_bot():
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("ERROR: Please replace 'YOUR_DISCORD_BOT_TOKEN' in the script with your actual bot token.")
        return
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    start_bot()
