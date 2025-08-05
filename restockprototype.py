import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import difflib

# In scrape_mtgstocks_sealed_prices, store both price and url:
def scrape_mtgstocks_sealed_prices():
    """
    Scrape MTGStocks sealed box set prices from their API and return as a dict:
    {box_set_name: {"price": price, "url": url}}
    """
    url = "https://api.mtgstocks.com/sealed"
    prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code} from MTGStocks API.")
        print(f"Response text: {response.text[:500]}")
        return prices
    try:
        data = response.json()
    except Exception as e:
        print(f"Error decoding JSON from MTGStocks API: {e}")
        print(f"Response text: {response.text[:500]}")
        return prices
    for set_data in data:
        for product in set_data.get("products", []):
            name = f"{set_data['name']} {product['name']}".strip()
            price = product.get("latestPrice", {}).get("average") or product.get("latestPrice", {}).get("market")
            product_id = product.get("id")
            # Build the correct sealed URL
            product_url_name = (
                f"{set_data['name']} {product['name']}"
                .lower()
                .replace(" ", "-")
                .replace(":", "")
                .replace("'", "")
                .replace(",", "")
                .replace(".", "")
            )
            sealed_url = f"https://www.mtgstocks.com/sealed/{product_id}-{product_url_name}" if product_id else None
            if price and sealed_url:
                prices[name.lower()] = {"price": float(price), "url": sealed_url}
    return prices

def get_domain(url):
    try:
        return re.search(r"https?://(?:www\.)?([^/]+)", url).group(1)
    except Exception:
        return url

# --- Begin: Minimal MTGWebSearchAgent for box set search ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class MTGWebSearchAgent:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1280,800")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def search_box_sets(self, query):
        # Use DuckDuckGo shopping vertical for more product-like results
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=shopping&iax=shopping"
        self.driver.get(search_url)
        time.sleep(2)
        results = []
        try:
            # Find the shopping results container
            shopping_container = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.wUznQh6YTPOEAjCVVIgH.KTqp6F7OjYVDWqCuvHC2"
            )
            # Each product listing is likely a child div or anchor inside this container
            product_cards = shopping_container.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            for card in product_cards:
                try:
                    title = card.text.strip()
                    href = card.get_attribute("href")
                    price = ""
                    # Try to extract price from the card text
                    price_match = re.search(r"\$\d[\d,\.]*", title)
                    if price_match:
                        price = price_match.group(0)
                    domain = get_domain(href)
                    results.append({
                        "domain": domain,
                        "title": title,
                        "url": href,
                        "snippet": price
                    })
                except Exception:
                    continue
                if len(results) >= 10:
                    break
            if not results:
                print("No shopping results found. Here is a portion of the page source:")
                print(self.driver.page_source[:1000])
        except Exception as e:
            print(f"Web search error: {e}")
        return results

    def close(self):
        if self.driver:
            self.driver.quit()
# --- End: Minimal MTGWebSearchAgent ---

class HermesModel:
    def __init__(self):
        # Initialize your Hermes model here if needed
        pass

    def generate(self, prompt: str) -> str:
        # Replace this with your actual Hermes model call
        print(f"[Hermes] Prompt: {prompt}")
        return "Hermes model response here."

def execute_web_search(query: str):
    agent = MTGWebSearchAgent()
    try:
        results = agent.search_box_sets(query)
    finally:
        agent.close()
    return results

def cost_to_value_search():
    """
    Find the best MTG box sets online with the highest profit margin compared to MTGStocks price.
    """
    print("💹 Cost-to-Value Search: Find the best MTG box set deals online!")
    print("⏳ Scraping MTGStocks sealed box set prices for reference...")
    mtgstocks_prices = scrape_mtgstocks_sealed_prices()
    print(f"✅ Loaded {len(mtgstocks_prices)} box set prices from MTGStocks.\n")

    # Expanded search variations including major stores
    queries = [
        "magic the gathering sealed booster box set",
        "mtg sealed booster box set",
        "magic the gathering booster box",
        "magic the gathering box set booster box",
        "magic the gathering box booster box",
        "magic the gathering box set sale booster box",
        "magic the gathering box sale booster box",
        "mtg box set sale booster box",
        "mtg box sale booster box",
        "magic the gathering booster box amazon",
        "magic the gathering booster box ebay ",
        "magic the gathering booster box tcgplayer ",
        "magic the gathering booster box walmart ",
        "magic the gathering booster box target ",
        "magic the gathering booster box amazon sale ",
        "magic the gathering booster box ebay sale ",
        "magic the gathering booster box tcgplayer sale ",
        "magic the gathering booster box walmart sale ",
        "magic the gathering booster box target sale ",
        "magic the gathering booster box amazon ",
        "magic the gathering booster box ebay ",
        "magic the gathering booster box tcgplayer ",
        "magic the gathering box walmart sale ",
        "magic the gathering box target sale",
        "gamestop magic the gathering booster box",
        "discounts magic the gathering booster box",
        "magic the gathering booster box 2025",
        "new magic the gathering booster box"
    ]

    all_results = []
    seen_urls = set()
    for q in queries:
        print(f"🔍 Searching online for: {q} ...")
        results = execute_web_search(q)
        for result in results:
            if result['url'] not in seen_urls:
                all_results.append(result)
                seen_urls.add(result['url'])

    print(f"\nHermes: Here are the combined results for your queries ({len(all_results)} unique listings):\n")
    for idx, result in enumerate(all_results, 1):
        print(f"{idx}. {result['domain']}")
        print(f"   Title: {result['title']}")
        print(f"   Link: {result['url']}")
        if result['snippet']:
            print(f"   Snippet: {result['snippet']}")
        print()

    # Automatically run cost-to-value search
    cost_to_value_compare(all_results, mtgstocks_prices)

def normalize_name(name):
    """Lowercase and remove non-alphanumeric for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', name.lower())

def cost_to_value_compare(search_results, mtgstocks_prices):
    print("\nCost-to-Value Comparison (Profitable Deals Only):")
    print(f"{'Online Listing':50} {'Online Price':>12} {'MTGStocks Name':40} {'MTGStocks Price':>16} {'Profit':>12}")
    print("-" * 140)
    found_profitable = False
    profitable_deals = []

    # Only allow these product types
    allowed_box_terms = [
        "booster box", "set booster box", "collector booster box", "draft booster box", "set box"
    ]

    def is_allowed_box(name):
        name = name.lower()
        return any(term in name for term in allowed_box_terms)

    # Terms to strip for set name extraction
    generic_terms = [
        "magic the gathering", "mtg", "booster box", "box set", "set booster box",
        "collector booster box", "draft booster box", "theme booster box", "bundle",
        "fat pack", "gift box", "sealed", "english", "new", "factory", "edition"
    ]

    def extract_set_name(title):
        name = title.lower()
        for term in generic_terms:
            name = name.replace(term, "")
        name = re.sub(r'[\(\)\[\]\d\-\:\!\|,\.]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    for result in search_results:
        title = result['title']
        snippet = result['snippet']
        url = result['url']
        online_price = None
        price_match = re.search(r"\$([\d,]+\.\d{2})", snippet or title)
        if price_match:
            online_price = float(price_match.group(1).replace(',', ''))
        else:
            continue

        # Only consider listings that look like booster/set boxes and NOT cases
        if not is_allowed_box(title) or "case" in title.lower():
            continue

        # Only consider MTGStocks entries that are booster/set boxes and NOT cases
        filtered_keys = [k for k in mtgstocks_prices if is_allowed_box(k) and "case" not in k.lower()]

        listing_set_name = extract_set_name(title)
        mtg_set_names = [extract_set_name(k) for k in filtered_keys]

        # Use a more flexible cutoff for fuzzy matching to allow matches off by one or two words,
        # but still do not allow it to match "case"
        close_matches = difflib.get_close_matches(listing_set_name, mtg_set_names, n=1, cutoff=0.5)
        best_match = None
        if close_matches:
            idx = mtg_set_names.index(close_matches[0])
            best_match = filtered_keys[idx]
            # Extra safety: double-check "case" is not in the matched MTGStocks name
            if "case" in best_match.lower():
                best_match = None

        if best_match:
            mtg_price = mtgstocks_prices[best_match]["price"]
            mtgstocks_url = mtgstocks_prices[best_match]["url"]
            profit = mtg_price - online_price
            if profit > 0:
                found_profitable = True
                print(f"{title[:48]:50} ${online_price:10,.2f} {best_match[:40]:40} ${mtg_price:14,.2f} ${profit:10,.2f}")
                print(f"  Online Link: {url}")
                print(f"  MTGStocks:   {mtgstocks_url}")
                print()
                if online_price < 1000:
                    profitable_deals.append({
                        "title": title,
                        "online_price": online_price,
                        "best_match": best_match,
                        "mtg_price": mtg_price,
                        "profit": profit,
                        "url": url,
                        "mtgstocks_url": mtgstocks_url
                    })
    if not found_profitable:
        print("No profitable deals found (online price is not lower than MTGStocks price).")
    else:
        # Filter for online price < $600
        filtered_deals = [d for d in profitable_deals if d["online_price"] < 600]
        # Sort by profit descending
        filtered_deals.sort(key=lambda x: x["profit"], reverse=True)

        # Deduplicate by fuzzy set name (so only the best deal per set is shown)
        unique_set_names = set()
        top_unique_deals = []
        for deal in filtered_deals:
            # Normalize for fuzzy matching
            norm_name = normalize_name(deal["best_match"])
            # Only add if not similar to any already added
            if not any(difflib.SequenceMatcher(None, norm_name, n).ratio() > 0.85 for n in unique_set_names):
                unique_set_names.add(norm_name)
                top_unique_deals.append(deal)
            if len(top_unique_deals) >= 3:
                break

        print("\n🏆 Top Profit Margin Deals (unique sets, online price < $600, booster/set boxes only):")
        for i, deal in enumerate(top_unique_deals):
            place = "Best Deal" if i == 0 else f"Runner Up {i}"
            mtgstocks_url = deal["mtgstocks_url"]
            print(f"\n{place}:")
            print(f"  Title: {deal['title']}")
            print(f"  Online Price: ${deal['online_price']:.2f}")
            print(f"  MTGStocks Name: {deal['best_match']}")
            print(f"  MTGStocks Price: ${deal['mtg_price']:.2f}")
            print(f"  Profit: ${deal['profit']:.2f}")
            print(f"  Online Link: {deal['url']}")
            print(f"  MTGStocks Link: {mtgstocks_url}")

            # Prompt user for action
            while True:
                user_input = input("\nWould you like to buy this item? (y = yes, n = next best match, q = quit): ").strip().lower()
                if user_input == "y":
                    print("Great! Here are the links again for your purchase:")
                    print(f"  Online Link: {deal['url']}")
                    print(f"  MTGStocks Link: {mtgstocks_url}")
                    return  # Exit after user accepts a deal
                elif user_input == "n":
                    break  # Show next best match
                elif user_input == "q":
                    print("Exiting without selecting a deal.")
                    return
                else:
                    print("Please enter 'y', 'n', or 'q'.")
        print("No more matches to show.")

def extract_price_from_page(url):
    """
    Visit a product page and try to extract the price.
    Only supports Amazon, eBay, and TCGPlayer/MTGPlayer for now.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text
        # Amazon
        if "amazon." in url:
            match = re.search(r'id="priceblock_ourprice".*?\$([\d,]+\.\d{2})', html)
            if not match:
                match = re.search(r'id="priceblock_dealprice".*?\$([\d,]+\.\d{2})', html)
            if match:
                return f"${match.group(1)}"
        # eBay
        elif "ebay." in url:
            match = re.search(r'itemprop="price"[^>]*content="([\d\.]+)"', html)
            if match:
                return f"${match.group(1)}"
            match = re.search(r'\$([\d,]+\.\d{2})', html)
            if match:
                return f"${match.group(1)}"
        # TCGPlayer/MTGPlayer
        elif "tcgplayer." in url or "mtgplayer." in url:
            match = re.search(r'\$([\d,]+\.\d{2})', html)
            if match:
                return f"${match.group(1)}"
    except Exception as e:
        print(f"Error extracting price from {url}: {e}")
    hermes = HermesModel()
    hermes_prompt = (
        "You are about to run the cost_to_value_search script. "
        "Here is what it does:\n"
        f"{cost_to_value_search.__doc__}\n"
        "How would you like to proceed?"
    )   
    hermes_response = hermes.generate(hermes_prompt)
    print(f"Hermes says: {hermes_response}\n")
    cost_to_value_search()

if __name__ == "__main__":
    cost_to_value_search()