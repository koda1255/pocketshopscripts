import ollama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import base64, io, time, random
from PIL import Image
from datetime import datetime

def chat(model, messages, stream=False):
    try:
        response = ollama.chat(model=model, messages=messages, stream=stream)
        return response if stream else response['message']['content']
    except Exception as e:
        return f"Error with Ollama: {e}"

class MTGWebSearchAgent:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1280,800")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            print(f"WebDriver setup error: {e}")

    def search_articles(self, query):
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}+magic+the+gathering+article"
        try:
            self.driver.get(search_url)
            time.sleep(2)  # Give time for JS to render

            selectors = [
                "#react-layout > div > div > div",  # your original
                "div#links",                        # classic DuckDuckGo
                "main",                             # generic
                "body"                              # fallback
            ]
            found = []
            seen_urls = set()
            container = None

            # Try each selector until we find one that works
            for sel in selectors:
                try:
                    container = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if container:
                        break
                except Exception:
                    continue

            if container:
                links = container.find_elements(By.TAG_NAME, "a")
            else:
                print("Main container not found, falling back to all <a> tags.")
                links = self.driver.find_elements(By.TAG_NAME, "a")

            for el in links:
                href = el.get_attribute("href")
                text = el.text.strip() if el.text else ""
                if (
                    href and text and
                    ("mtg" in href.lower() or "magic" in href.lower() or "gathering" in href.lower()) and
                    href not in seen_urls
                ):
                    found.append({"title": text, "url": href})
                    seen_urls.add(href)
                if len(found) >= 3:
                    break

            if not found:
                print("No relevant links found in search results.")

            return found
        except Exception as e:
            print(f"Article search error: {e}")
            return []

    def extract_article_body(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Try common containers first
            for selector in ['article', 'main', 'div#content', 'div.article', 'div.post', 'div.entry-content']:
                el = soup.select_one(selector)
                if el and el.get_text(strip=True):
                    text = el.get_text(" ", strip=True)
                    return ' '.join(text.split())[:4000]
            # Fallback: get the largest block of text from any div
            divs = soup.find_all('div')
            largest = max(divs, key=lambda d: len(d.get_text(strip=True)), default=None)
            if largest:
                text = largest.get_text(" ", strip=True)
                return ' '.join(text.split())[:4000]
            # Fallback: whole page text
            text = soup.get_text(" ", strip=True)
            return ' '.join(text.split())[:4000]
        except Exception as e:
            print(f"Article extraction error: {e}")
            return ""

    def extract_snippets_from_search(self):
        """Extracts visible snippets from DuckDuckGo search results."""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            snippets = []
            # DuckDuckGo result snippets are often in <div class="result__snippet"> or similar
            for div in soup.find_all('div', class_='result__snippet'):
                text = div.get_text(" ", strip=True)
                if text:
                    snippets.append(text)
            # Fallback: grab all <span> with a lot of text
            if not snippets:
                for span in soup.find_all('span'):
                    text = span.get_text(" ", strip=True)
                    if len(text) > 40:
                        snippets.append(text)
            return "\n".join(snippets[:5])  # Return up to 5 snippets
        except Exception as e:
            print(f"Snippet extraction error: {e}")
            return ""

    def take_screenshot_with_analysis(self, url):
        try:
            self.driver.get(url)
            # Wait explicitly for the body tag to ensure the page is loaded
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            screenshot = self.driver.get_screenshot_as_png()
            time.sleep(random.uniform(2, 4))
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            clean_text = self.extract_article_body()
            return img_base64, clean_text, image
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None, "", None

    def _get_system_prompt(self):
        return f"You are a Magic: The Gathering financial analyst. Timestamp: {datetime.now().isoformat()}"

    def analyze_mtg_data_with_image(self, prompt, image_base64, page_text=""):
        system_prompt = (
            "You are a trend watcher and information specialist. "
            "Your task is to gather and summarize Magic: The Gathering card data and trends "
            "from the provided DuckDuckGo search result. Focus on extracting relevant card information, "
            "pricing, and any notable trends or news."
        )
        user_prompt = (
            f"Please analyze the following Magic: The Gathering website screenshot and extract card data, pricing, and trends. "
            f"This is from a DuckDuckGo query. Page text: {page_text[:1000]}"
        )
        return chat(
            model="hermes3",
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt, 'images': [image_base64]}
            ]
        )

    def analyze_mtg_data_text_only(self, prompt, page_text):
        analysis_prompt = f"Analyze this MTG website text and extract card info. Page content: {page_text}"
        return chat(
            model="hermes3",
            messages=[
                {'role': 'system', 'content': self._get_system_prompt()},
                {'role': 'user', 'content': analysis_prompt}
            ]
        )

    def process_mtg_query(self, user_prompt):
        print(f"Processing MTG query: {user_prompt}")
        article_links = self.search_articles(user_prompt)
        search_snippets = self.extract_snippets_from_search()
        if not article_links:
            return f"Could not find relevant articles for: {user_prompt}\n\nSearch snippets:\n{search_snippets}"
        result = article_links[0]
        screenshot_b64, article_text, screenshot_img = self.take_screenshot_with_analysis(result['url'])
        if screenshot_img:
            screenshot_img.save("mtg_article_screenshot.png")
        analysis = self.analyze_mtg_data_with_image(user_prompt, screenshot_b64, article_text) if screenshot_b64 else self.analyze_mtg_data_text_only(user_prompt, article_text)
        return f"Article: {result['title']}\nURL: {result['url']}\n\nExtracted Content:\n{article_text}\n\nSearch snippets:\n{search_snippets}\n\nAnalysis:\n{analysis}"

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    agent = MTGWebSearchAgent()
    try:
        while True:
            user_query = input("Enter your Magic: The Gathering search query (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break
            print("="*60)
            result = agent.process_mtg_query(user_query)
            print(result)
            print("="*60)
            time.sleep(2)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        agent.close()

if __name__ == "__main__":
    main()