
import discord
import json
import os
from EbayMTGCardLister import main as run_lister # Import the main function

# --- Discord Bot Configuration ---
# IMPORTANT: Replace "YOUR_DISCORD_BOT_TOKEN" with your actual bot token.
# It's highly recommended to set this as an environment variable for security.
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Check for the !listcards command
    if message.content.startswith("!listcards"):
        await message.channel.send("Received command! Starting the eBay listing process...")

        try:
            # --- Run the eBay Lister Script ---
            # The lister script reads 'products.json' directly.
            # We will capture the print output to send back to Discord.
            
            import io
            import sys
            
            # Redirect stdout to capture the output of the script
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()

            # Call the main function from your lister script
            run_lister()

            # Restore stdout
            sys.stdout = old_stdout
            
            # Get the output from the lister
            lister_output = captured_output.getvalue()

            # --- Send the results back to Discord ---
            # Discord has a 2000 character limit per message.
            # We'll split the output into chunks if it's too long.
            if len(lister_output) > 1990:
                await message.channel.send("Lister output is very long. Sending in chunks:")
                for i in range(0, len(lister_output), 1990):
                    await message.channel.send(f"```
{lister_output[i:i+1990]}
```")
            else:
                await message.channel.send(f"```
{lister_output}
```")

            await message.channel.send("✅ eBay listing process complete.")

        except FileNotFoundError:
            await message.channel.send("❌ Error: `products.json` not found. Please make sure the file exists.")
        except json.JSONDecodeError:
            await message.channel.send("❌ Error: `products.json` contains invalid JSON. Please check the file format.")
        except Exception as e:
            await message.channel.send(f"An unexpected error occurred: {e}")

def start_bot():
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("Please replace 'YOUR_DISCORD_BOT_TOKEN' in the script with your actual bot token.")
        return
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    start_bot()
