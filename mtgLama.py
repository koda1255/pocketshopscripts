from ollama import chat
import chromadb
import subprocess
import json
import os
from datetime import datetime
import traceback
import re
from mtgstocksPriceDatabasescraper import get_card_price
from gemmacardidentifier import identify_card_from_image
from trendnewscollector import MTGWebSearchAgent
from cost_to_value_search import cost_to_value_search
import difflib

# Use PersistentClient with a specific path
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Try to create collection, handle if it already exists
try:
    collection = chroma_client.create_collection(name="mtgchathistory")
except Exception as e:
    # Collection might already exist, try to get it
    try:
        collection = chroma_client.get_collection(name="mtgchathistory")
    except:
        print(f"ChromaDB setup failed: {e}")
        print("Continuing without chat history...")
        collection = None

# Debug mode flag
DEBUG_MODE = False

def debug_print(message, error=None):
    """Print debug messages when DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}")
        if error:
            print(f"[ERROR] {str(error)}")
            print(f"[TRACEBACK] {traceback.format_exc()}")

def get_present_datetime():
    """Get the current date and time in various formats"""
    now = datetime.now()
    return {
        "iso_format": now.isoformat(),
        "readable": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "time_12h": now.strftime("%I:%M:%S %p"),
        "short_format": now.strftime("%m/%d/%Y %H:%M"),
        "long_format": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
        "unix_timestamp": int(now.timestamp()),
        "components": {
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
            "month_name": now.strftime("%B")
        },
        "timezone": "Local",
        "knowledge_cutoff": "April 2024"  # Fixed: Realistic knowledge cutoff date
    }

def find_brave_search_tool():
    """Find the bravesearchtool.py script in various locations"""
    possible_paths = [
        # Same directory as this script
        os.path.join(os.path.dirname(__file__), 'bravesearchtool.py'),
        # Current working directory
        os.path.join(os.getcwd(), 'bravesearchtool.py'),
        # Parent directory
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bravesearchtool.py'),
        # Specific path based on your structure
        r'c:\Users\dakot\OneDrive\Desktop\localai\bravesearchtool.py',
        r'c:\Users\dakot\OneDrive\Desktop\localai\.venv\bravesearchtool.py',
    ]
    
    debug_print("Looking for bravesearchtool.py script...")
    for path in possible_paths:
        debug_print(f"Checking: {path}")
        if os.path.exists(path):
            debug_print(f"Found bravesearchtool.py at: {path}")
            return path
    
    debug_print("bravesearchtool.py not found in any expected location")
    return None

def execute_web_search(query):
    """Execute web search using bravesearchtool.py"""
    debug_print(f"Starting web search for: '{query}'")
    
    try:
        # Find the script
        script_path = find_brave_search_tool()
        if not script_path:
            error_msg = "❌ Search Error: bravesearchtool.py script not found"
            debug_print(error_msg)
            return None
        
        # Prepare the command with proper flags
        cmd = ['python', script_path, '--query', query]
        debug_print(f"Running command: {' '.join(cmd)}")
        
        # Get the working directory (directory containing the script)
        working_dir = os.path.dirname(script_path)
        debug_print(f"Working directory: {working_dir}")
        
        # Set environment variables to handle UTF-8 encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Execute the search
        debug_print("Executing subprocess...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30,
            check=False,
            env=env,
            encoding='utf-8',
            errors='replace'  # Replace problematic characters instead of failing
        )
        
        debug_print(f"Subprocess completed with return code: {result.returncode}")
        debug_print(f"STDOUT length: {len(result.stdout) if result.stdout else 0}")
        debug_print(f"STDERR length: {len(result.stderr) if result.stderr else 0}")
        
        if result.returncode == 0:
            if result.stdout.strip():
                debug_print("Search completed successfully")
                # Clean up any problematic characters for display
                clean_output = result.stdout.strip().encode('ascii', 'ignore').decode('ascii')
                return clean_output if clean_output else result.stdout.strip()
            else:
                debug_print("Search completed but no output")
                return None
        else:
            error_msg = f"Search Error (code {result.returncode}): {result.stderr.strip() if result.stderr else 'Unknown error'}"
            debug_print(error_msg)
            return None
            
    except subprocess.TimeoutExpired:
        debug_print("Search Error: Search timed out after 30 seconds")
        return None
    except FileNotFoundError as e:
        debug_print(f"Search Error: Python or script not found - {str(e)}", e)
        return None
    except Exception as e:
        debug_print("Web search execution failed", e)
        return None

def should_use_web_search(prompt):
    """Determine if the prompt requires web search"""
    search_keywords = [
        'latest', 'recent', 'current', 'new', 'today', 'now', 'what is', 'whats',
        'episode', 'season', 'show', 'tv', 'series', 'news', 'update', 'when',
        'rick and morty', 'search', 'find', 'look up', '2024', '2025'
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in search_keywords)

def should_use_datetime(prompt):
    """Determine if the prompt requires datetime info"""
    time_keywords = ['time', 'date', 'today', 'now', 'current', 'when is']
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in time_keywords)

def should_use_card_price(prompt):
    """Determine if the prompt requires card price information"""
    keywords = ['card price', 'mtg price', 'how much is', 'value of', 'price of']
    return any(k in prompt.lower() for k in keywords)

def should_use_card_image(prompt):
    """Determine if the prompt requires card image identification"""
    keywords = ['identify card image', 'what card is this image', 'card from image']
    return any(k in prompt.lower() for k in keywords)

def should_use_trend_news(prompt):
    """Determine if the prompt requires trend/news collector"""
    keywords = ['news', 'trend', 'trending', 'article', 'finance', 'financial', 'market']
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in keywords)

def should_use_cost_to_value(prompt):
    """Determine if the prompt requires cost-to-value analysis"""
    keywords = [
        'cost to value', 'profit margin', 'best box set', 'box set deal', 'sealed box set',
        'best set to buy', 'best new set', 'cost value', 'value search', 'investment', 'roi',
        'cost to value function', 'cost-to-value', 'run cost to value', 'box set profit', 'mtg box set'
    ]
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in keywords)

def toggle_debug():
    """Toggle debug mode"""
    global DEBUG_MODE
    DEBUG_MODE = not DEBUG_MODE
    print(f"🐛 Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")

# --- Function registry with keywords ---
FUNCTION_REGISTRY = [
    {
        "name": "DateTime",
        "func": lambda: print(f"Current date and time: {get_present_datetime()['readable']}"),
        "keywords": ["date", "time", "now", "current", "today"]
    },
    {
        "name": "Card Price Lookup",
        "func": lambda: print(get_card_price(input("Enter the card name to look up price: ").strip())),
        "keywords": ["card price", "mtg price", "how much is", "value of", "price of"]
    },
    {
        "name": "Card Image Identification",
        "func": lambda: print(identify_card_from_image(input("Enter the image file path (jpg/png): ").strip())),
        "keywords": ["card identifier", "card image identification", "identify card image", "what card is this image", "card from image"]
    },
    {
        "name": "Web Search",
        "func": lambda: print("Web search function is not yet implemented."),
        "keywords": ["search", "find", "look up", "web search", "latest", "recent", "current", "news", "update"]
    },
    {
        "name": "Trend/News Collector",
        "func": run_trend_news_collector,
        "keywords": ["news", "trend", "trending", "article", "finance", "market"]
    },
    {
        "name": "Cost-to-Value Search",
        "func": cost_to_value_search,
        "keywords": [
            "cost to value", "profit margin", "best box set", "box set deal", "sealed box set",
            "best set to buy", "best new set", "cost value", "value search", "investment", "roi",
            "cost to value function", "cost-to-value", "run cost to value", "box set profit", "mtg box set"
        ]
    }
]

def parse_explicit_function_request(prompt, available_functions):
    """
    Check if the user prompt explicitly asks to use a function by name.
    Returns a list of function names to trigger, using fuzzy matching.
    """
    available_functions = [f["name"] for f in FUNCTION_REGISTRY]

    lower_prompt = prompt.lower()
    triggered = []
    for func in available_functions:
        func_words = func.lower().replace("-", " ").split()
        # If most words in the function name are present or close in the prompt, trigger it
        match_count = sum(
            any(difflib.SequenceMatcher(None, word, w).ratio() > 0.7 for w in lower_prompt.split())
            for word in func_words
        )
        if match_count >= max(1, len(func_words) - 1):  # allow one word to be off
            triggered.append(func)
    return list(set(triggered))

# Define a reusable system prompt for generating conversational opinions/summaries
CONVERSATIONAL_OPINION_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "When given information or search results, respond with a short, conversational answer or opinion (1-2 sentences) "
    "that summarizes or reacts to the content in a friendly, accessible way."
)

def run_trend_news_collector():
    """Prompt user for a trend/news query, run the trendnewscollector, and return its result."""
    user_query = input("Enter a Magic: The Gathering news or trend to search for: ").strip()
    if not user_query:
        print("No query provided. Skipping trend/news search.")
        return ""
    agent = MTGWebSearchAgent()
    try:
        result = agent.process_mtg_query(user_query)
        print("\n=== Trend/News Collector Result ===")
        print(result)
        print("=== End of Trend/News Collector Result ===\n")
        # Now get a short opinion from the chat model
        opinion_prompt = (
            "Give a short, conversational opinion (1-2 sentences) about the Magic: The Gathering news/trend below:\n\n"
            f"{result}\n\nOpinion:"
        )
        opinion = chat(
            model="hermes3",
            messages=[
                {'role': 'system', 'content': CONVERSATIONAL_OPINION_SYSTEM_PROMPT},
                {'role': 'user', 'content': opinion_prompt}
            ]
        )
        print("🤖 Assistant's Opinion:", opinion.strip())
        return result
    finally:
        agent.close()

def run_web_search_collector():
    """Prompt user for a web search query, run the web search, and return its result."""
    user_query = input("Enter a web search query: ").strip()
    if not user_query:
        print("No query provided. Skipping web search.")
        return ""
    print("🔍 Searching the web...")
    search_data = execute_web_search(user_query)
    if search_data:
        print("\n=== Web Search Result ===")
        print(search_data)
        print("=== End of Web Search Result ===\n")
        # Now get a short summary/opinion from the chat model
        opinion_prompt = (
            "Give a short, conversational summary (1-2 sentences) about the web search result below:\n\n"
            f"{search_data}\n\nSummary:"
        )
        opinion = chat(
            model="hermes3",
            messages=[
                {'role': 'system', 'content': CONVERSATIONAL_OPINION_SYSTEM_PROMPT},
                {'role': 'user', 'content': opinion_prompt}
            ]
        )
        print("🤖 Assistant's Summary:", opinion.strip())
        return search_data
    else:
        print("⚠️  No current search results found.")
        return ""

# --- Function registry with keywords ---

def show_function_menu():
    print("\n=== Function Menu ===")
    for idx, f in enumerate(FUNCTION_REGISTRY, 1):
        print(f"{idx}. {f['name']} (keywords: {', '.join(f['keywords'])})")
    print("=====================")

def get_functions_from_prompt(prompt):
    prompt_lower = prompt.lower()
    triggered = []
    for f in FUNCTION_REGISTRY:
        if any(kw in prompt_lower for kw in f["keywords"]):
            triggered.append(f)
    return triggered

# Main chat loop
history = []
current_time_info = get_present_datetime()
print("🤖 Chat Assistant with Function Calling - Type 'quit' or 'exit' to end")
print(f"📅 Current Time: {current_time_info['readable']}")
print("🔧 Available functions: " + ", ".join(f["name"] for f in FUNCTION_REGISTRY))
print("🐛 Debug mode:", "ON" if DEBUG_MODE else "OFF")

# Test if bravesearchtool.py is found at startup
script_path = find_brave_search_tool()
if script_path:
    print(f"✅ Found bravesearchtool.py at: {script_path}")
else:
    print("❌ Warning: bravesearchtool.py not found - web search will not work")

print("-" * 80)

while True:
    prompt = input("\n👤 User: ")

    if prompt.lower() in ['quit', 'exit', 'bye']:
        print("👋 Goodbye!")
        break

    if prompt.lower() == "menu":
        show_function_menu()
        menu_choice = input("Select a function by number (or press Enter to cancel): ").strip()
        if menu_choice.isdigit():
            idx = int(menu_choice) - 6
            if 0 <= idx < len(FUNCTION_REGISTRY):
                FUNCTION_REGISTRY[idx]["func"]()
        continue

    if not prompt.strip():
        continue

    # CARD IMAGE IDENTIFICATION: auto-call if image path is present
    match = re.search(r'([A-Za-z]:\\[^\s]+?\.(jpg|png))', prompt, re.IGNORECASE)
    if match:
        image_path = match.group(1)
        print(f"🖼️ Running Card Image Identification on: {image_path}")
        card_info = identify_card_from_image(image_path)
        print(card_info)
        continue

    # CARD IMAGE IDENTIFICATION: explicit request, but no image path yet
    if "card identifier" in prompt.lower() or "card image identification" in prompt.lower():
        image_path = input("Please provide the image file path (jpg/png): ").strip()
        if image_path:
            print(f"🖼️ Running Card Image Identification on: {image_path}")
            card_info = identify_card_from_image(image_path)
            print(card_info)
        else:
            print("⚠️  No image path provided.")
        continue

    # Detect which functions are relevant
    triggered_functions = get_functions_from_prompt(prompt)
    print("\n🔧 The following functions may help answer your question: " +
          (", ".join(f["name"] for f in triggered_functions) if triggered_functions else "None"))
    print("Type 'menu' to see all available functions at any time.")

    # If no functions are triggered, show the full function menu automatically
    if not triggered_functions:
        print("\nNo special functions detected. Here is a menu of all available functions:")
        show_function_menu()
        menu_choice = input("Select a function by number (or press Enter to skip): ").strip()
        if menu_choice.isdigit():
            idx = int(menu_choice) - 1
            if 0 <= idx < len(FUNCTION_REGISTRY):
                FUNCTION_REGISTRY[idx]["func"]()
        continue

    # Always allow user to pick from all functions (with highlights)
    for idx, f in enumerate(FUNCTION_REGISTRY, 1):
        highlight = " <==" if f in triggered_functions else ""
        print(f"  {idx}. {f['name']}{highlight}")
    user_choice = input("Which would you like to use? (Type numbers separated by commas, or press Enter to skip all): ").strip()
    if not user_choice:
        continue
    try:
        selected_indices = [int(x.strip()) for x in user_choice.split(",") if x.strip().isdigit()]
        for idx in selected_indices:
            if 0 < idx <= len(FUNCTION_REGISTRY):
                FUNCTION_REGISTRY[idx-1]["func"]()
    except Exception:
        print("Invalid input. Skipping all functions.")

    # Add to collection if available
    if collection:
        try:
            collection.add(
                documents=[prompt],
                ids=[f"user_{len(history)}_{hash(prompt)}"]
            )
            relevant_list = collection.query(
                query_texts=[prompt],
                n_results=3
            )
            clean_list = relevant_list['documents'][0]
        except:
            clean_list = []
    else:
        clean_list = []

    # Create system prompt with better structure
    system_parts = [
        "You are a helpful AI assistant with access to current information through function calls.",
        f"Your knowledge cutoff is April 2024, but you can access current information through functions."
    ]

    # Add function results if available
    if search_results:
        system_parts.append(
            f"\n=== CURRENT WEB SEARCH RESULTS ===\n{search_results}\n=== END SEARCH RESULTS ==="
        )
        system_parts.append(
            "IMPORTANT: Use ONLY the web search results above to answer the user's question. "
            "After your answer, explain in 2-3 sentences how you used the web search results to find the answer. "
            "Be specific about which facts or phrases from the search you relied on."
        )
    if datetime_info:
        system_parts.append(f"\n=== CURRENT DATE/TIME ===\n{datetime_info}\n=== END DATE/TIME ===")
    if card_price_info:
        system_parts.append(f"\n=== CARD PRICE LOOKUP ===\n{card_price_info}\n=== END CARD PRICE ===")
    if card_image_info:
        system_parts.append(f"\n=== CARD IMAGE IDENTIFICATION ===\n{card_image_info}\n=== END CARD IMAGE ===")

    # Add conversation context
    if clean_list:
        system_parts.append(f"\nRecent conversation context: {clean_list[-3:]}")

    # Add final instructions
    system_parts.append("\nInstructions:")
    system_parts.append("- If search results are provided above, USE THEM as your primary source")
    system_parts.append("- Be accurate and cite the current information when available")
    system_parts.append("- If search results show an error, explain what went wrong")
    

    SYSTEM_PROMPT = "\n".join(system_parts)

    # Get AI response
    try:
        stream = chat(
            model="hermes3",
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            options={"temperature": 0.1},
            stream=True
        )

        # Add user message to history
        history.append(f"User: {prompt}")
        
        # Stream and collect AI response
        message = ""
        print("\n🤖 Assistant: ", end='', flush=True)
        for chunk in stream:
            message += chunk['message']['content']
            print(chunk['message']['content'], end='', flush=True)
        
        print()  # New line after response
        
        # Add AI response to history and collection
        history.append(f"Assistant: {message}")
        if collection:
            try:
                collection.add(
                    documents=[message], 
                    ids=[f"assistant_{len(history)}_{hash(message)}"]
                )
            except:
                pass
        
        # Keep history manageable
        if len(history) > 20:
            history = history[-20:]
            
    except Exception as e:
        print(f"❌ Error getting AI response: {str(e)}")
        debug_print("AI response error", e)
