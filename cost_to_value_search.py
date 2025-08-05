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

def scrape_mtgstocks_sealed_prices():
    """
    Scrape MTGStocks sealed box set prices from their API and return as a dict: {box_set_name: price}
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
            if price:
                prices[name.lower()] = float(price)
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
        "magic the gathering sealed box set",
        "mtg sealed box set",
        "magic the gathering booster box",
        "mtg booster box",
        "magic the gathering box set",
        "magic the gathering box",
        "magic the gathering box set sale",
        "magic the gathering box sale",
        "mtg box set sale",
        "mtg box sale",
        "magic the gathering box set amazon",
        "magic the gathering box set ebay",
        "magic the gathering box set tcgplayer",
        "magic the gathering box set walmart",
        "magic the gathering box set target",
        "magic the gathering box set amazon sale",
        "magic the gathering box set ebay sale",
        "magic the gathering box set tcgplayer sale",
        "magic the gathering box set walmart sale",
        "magic the gathering box set target sale",
        "magic the gathering box amazon",
        "magic the gathering box ebay",
        "magic the gathering box tcgplayer",
        "magic the gathering box walmart",
        "magic the gathering box target",
        "magic the gathering box amazon sale",
        "magic the gathering box ebay sale",
        "magic the gathering box tcgplayer sale",
        "magic the gathering box walmart sale",
        "magic the gathering box target sale",
        "mtg box set amazon",
        "mtg box set ebay",
        "mtg box set tcgplayer",
        "mtg box set walmart",
        "mtg box set target",
        "mtg box set amazon sale",
        "mtg box set ebay sale",
        "mtg box set tcgplayer sale",
        "mtg box set walmart sale",
        "mtg box set target sale",
        "mtg box amazon",
        "mtg box ebay",
        "mtg box tcgplayer",
        "mtg box walmart",
        "mtg box target",
        "mtg box amazon sale",
        "mtg box ebay sale",
        "mtg box tcgplayer sale",
        "mtg box walmart sale",
        "mtg box target sale"
        
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
        "fat pack", "gift box", "case", "sealed", "english", "new", "factory", "edition"
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

        # Only consider listings that look like booster/set boxes
        if not is_allowed_box(title):
            continue

        is_case = "case" in title.lower()
        if is_case:
            filtered_keys = [k for k in mtgstocks_prices if "case" in k.lower()]
        else:
            filtered_keys = [k for k in mtgstocks_prices if "case" not in k.lower()]

        # Only consider MTGStocks entries that are booster/set boxes
        filtered_keys = [k for k in filtered_keys if is_allowed_box(k)]

        listing_set_name = extract_set_name(title)
        mtg_set_names = [extract_set_name(k) for k in filtered_keys]

        close_matches = difflib.get_close_matches(listing_set_name, mtg_set_names, n=1, cutoff=0.5)
        best_match = None
        if close_matches:
            idx = mtg_set_names.index(close_matches[0])
            best_match = filtered_keys[idx]

        if best_match:
            mtg_price = mtgstocks_prices[best_match]
            profit = mtg_price - online_price
            if profit > 0:
                found_profitable = True
                mtgstocks_url = f"https://www.mtgstocks.com/products?q={'+'.join(best_match.split())}"
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
        filtered_deals = [d for d in profitable_deals if d["online_price"] < 600]
        filtered_deals.sort(key=lambda x: x["profit"], reverse=True)
        print("\n🏆 Top 3 Best Profit Margin Deals (online price < $600, booster/set boxes only):")
        for i, deal in enumerate(filtered_deals[:3]):
            place = "Best Deal" if i == 0 else f"Runner Up {i}"
            print(f"\n{place}:")
            print(f"  Title: {deal['title']}")
            print(f"  Online Price: ${deal['online_price']:.2f}")
            print(f"  MTGStocks Name: {deal['best_match']}")
            print(f"  MTGStocks Price: ${deal['mtg_price']:.2f}")
            print(f"  Profit: ${deal['profit']:.2f}")
            print(f"  Online Link: {deal['url']}")
            print(f"  MTGStocks Link: {deal['mtgstocks_url']}")

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
    return None

if __name__ == "__main__":
    # Use the HermesModel to prompt at the start
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