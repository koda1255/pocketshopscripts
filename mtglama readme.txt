# MTG Lama - AI-Powered Magic: The Gathering Toolkit

MTG Lama is a sophisticated, command-line interface (CLI) assistant designed for Magic: The Gathering enthusiasts, players, and collectors. It leverages the power of local Large Language Models (LLMs) through Ollama to provide a conversational experience, augmented with a suite of specialized tools for real-time data retrieval and analysis.

Whether you need to check a card's price, identify a card from an image, research market trends, or analyze the value of a sealed box, MTG Lama is your all-in-one assistant.

## Features

-   **Conversational AI**: Chat with an AI that understands MTG-specific queries, powered by a local LLM (`hermes3`).
-   **Card Price Lookup**: Get up-to-date market prices for any MTG card by querying a locally-built card database.
-   **Card Image Identification**: Identify an MTG card and its details directly from a local image file.
-   **Live Web Search**: Perform general web searches for the latest information, rules, or articles using the Brave Search API.
-   **MTG News & Trend Analysis**: Fetches and summarizes recent MTG news and financial trends from around the web.
-   **Cost-to-Value Analysis**: Analyzes the potential profitability of sealed MTG products to help with investment decisions.
-   **Persistent Chat History**: Remembers past conversations using a local ChromaDB vector database, providing better context for follow-up questions.
-   **Interactive Function Menu**: Suggests relevant tools based on your prompt and allows you to manually select functions to run.

## Setup and Installation

### 1. Prerequisites

-   **Python 3.8+**: Make sure you have a modern version of Python installed.
-   **Ollama**: You must have Ollama installed and running on your system.
-   **Brave Search API Key**: You need a free API key from Brave Search for the web search functionality.

### 2. Installation

1.  **Clone or download the project files** into a single directory.

2.  **Install Python dependencies**. It's recommended to use a virtual environment.
    ```bash
    # Create a virtual environment (optional but recommended)
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

    # Install the required packages
    pip install ollama chromadb requests beautifulsoup4 selenium webdriver-manager Pillow python-dotenv
    ```
    *(Note: Some dependencies are for the tool scripts that `mtgLama.py` calls.)*

3.  **Set up the Ollama Model**:
    Pull the `hermes3` model, which is used by the assistant for its conversational abilities.
    ```bash
    ollama pull hermes3
    ```

4.  **Configure API Keys**:
    Create a file named `.env` in the same directory as `bravesearchtool.py`. Add your Brave Search API key to this file:
    ```env
    # .env file
    BRAVE_API_KEY="YOUR_BRAVE_SEARCH_API_KEY_HERE"
    ```

### 3. Build the Card Database (Optional but Recommended)

The card price lookup tool relies on a local database of card prices scraped from MTGStocks. To enable this feature, you need to run the scraper script first.

```bash
python mtgstocksPriceDatabasescraper.py
```

-   When you run this script, it will ask how many sets you want to scrape.
-   This process can take a significant amount of time, but it creates a robust local database (`mtg_cards_db`) for fast and reliable price lookups.
-   The script can be run again later to update the database with new sets.

## Usage

To start the assistant, run the `mtgLama.py` script from your terminal:

```bash
python mtgLama.py
```

You will be greeted by the assistant. You can then type your questions or commands.

### Example Prompts

-   `What is the price of Lightning Bolt?`
-   `run cost to value`
-   `search for the latest news on Modern Horizons 3`
-   `what time is it?`
-   `identify card from image C:\Users\Me\Desktop\card.jpg`

### Special Commands

-   `menu`: Manually display the list of all available functions.
-   `debug`: Toggle debug mode on/off for more verbose output, which is useful for troubleshooting.
-   `quit` or `exit`: Exit the application.

## How It Works

1.  **Main Loop (`mtgLama.py`)**: This script is the central orchestrator. It handles user input, manages the conversation flow, and interacts with the LLM.
2.  **Function Registry & Detection**: When you enter a prompt, the script checks for keywords to suggest relevant tools (e.g., seeing "price of" suggests the "Card Price Lookup" tool). It then displays a menu of suggested and available functions.
3.  **Tool Execution**: You can select one or more tools to run. Each tool is a Python function that performs a specific task, such as scraping a website, calling an API, or performing a calculation.
4.  **LLM Interaction**: The results from the executed tools are formatted and combined with your original prompt and recent chat history. This entire package is sent as context to the Ollama model (`hermes3`), which then generates a comprehensive, conversational, and context-aware response.
5.  **Vector Database (`ChromaDB`)**: To maintain conversation context, each user prompt and AI response pair is stored in a local ChromaDB vector database. When you ask a new question, the database is queried for relevant past interactions, which are then included in the prompt to the LLM.

## Component Scripts

MTG Lama is a modular system that relies on several key scripts to provide its functionality:

-   **`bravesearchtool.py`**: A command-line wrapper for the Brave Search API. It's called as a subprocess to perform live web searches.
-   **`mtgstocksPriceDatabasescraper.py`**: A powerful scraper for MTGStocks.com. It builds and maintains a local ChromaDB database of all MTG cards and their prices. The `get_card_price` function in the main app queries this database.
-   **`gemmacardidentifier.py`**: Identifies card details from an image file by sending it to a local multimodal LLM via Ollama.
-   **`trendnewscollector.py`**: Uses Selenium to perform web searches for MTG news and articles. It extracts content from the top results and uses an LLM to provide a summary or analysis.
-   **`cost_to_value_search.py`**: A tool to analyze the investment potential of sealed MTG products. It scrapes online stores for current prices and compares them against the market value from MTGStocks to find profitable deals.

