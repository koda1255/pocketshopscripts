import json
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import re

class MTGCardImageScraper:
    def __init__(self, json_file_path, output_dir="card_images"):
        self.json_file_path = json_file_path
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def sanitize_filename(self, filename):
        """Remove or replace characters that aren't valid in filenames"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def load_cards_data(self):
        """Load the MTG cards data from JSON file"""
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    def save_cards_data(self, cards_data):
        """Save the updated cards data back to the original JSON file"""
        with open(self.json_file_path, 'w', encoding='utf-8') as file:
            json.dump(cards_data, file, indent=2, ensure_ascii=False)
    
    def get_image_url_from_page(self, card_url):
        """Extract the card image URL from the MTG Stocks page"""
        try:
            response = self.session.get(card_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Primary selector - the exact location you provided
            primary_selectors = [
                '#wrapper > div > div > div > div.col-lg-11 > ng-component > div:nth-child(2) > div > div > div > div.col-md-3.col-6.ps-0.pe-0.text-center > mtg-print-image img',
                '#wrapper > div > div > div > div.col-lg-11 > ng-component > div:nth-child(2) > div > div > div > div.col-md-3.col-6.ps-0.pe-0.text-center > mtg-print-image',
                'mtg-print-image img',
                'mtg-print-image'
            ]
            
            # Try the primary selectors first
            for selector in primary_selectors:
                element = soup.select_one(selector)
                if element:
                    # If it's an img tag, get the src
                    if element.name == 'img' and element.get('src'):
                        img_url = element['src']
                    else:
                        # If it's the mtg-print-image component, look for img inside it
                        img_element = element.find('img')
                        if img_element and img_element.get('src'):
                            img_url = img_element['src']
                        else:
                            continue
                    
                    # Convert relative URLs to absolute URLs
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(card_url, img_url)
                    
                    print(f"    🎯 Found image using selector: {selector}")
                    return img_url
            
            # Fallback selectors if the primary ones don't work
            fallback_selectors = [
                'img.card-image',
                'img[alt*="card"]',
                '.card-image img',
                'img[src*="card"]',
                'img[src*="gatherer"]',
                'img[src*="scryfall"]',
                '.col-md-3 img',
                '.text-center img'
            ]
            
            for selector in fallback_selectors:
                img_element = soup.select_one(selector)
                if img_element and img_element.get('src'):
                    img_url = img_element['src']
                    # Convert relative URLs to absolute URLs
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(card_url, img_url)
                    
                    print(f"    🔄 Found image using fallback selector: {selector}")
                    return img_url
            
            # Last resort: look for any image that might be the card
            print("    🔍 Trying last resort - scanning all images...")
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src', '')
                alt = img.get('alt', '').lower()
                class_list = ' '.join(img.get('class', []))
                
                if src and (
                    any(keyword in alt for keyword in ['card', 'magic', 'mtg']) or
                    any(keyword in src.lower() for keyword in ['card', 'gatherer', 'scryfall', 'mtg']) or
                    any(keyword in class_list.lower() for keyword in ['card', 'print'])
                ):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(card_url, src)
                    
                    print(f"    🎲 Found potential image: {src}")
                    return src
                    
            return None
            
        except Exception as e:
            print(f"    ❌ Error fetching image URL from {card_url}: {e}")
            return None
    
    def download_image(self, image_url, file_path):
        """Download an image from URL and save it to file_path"""
        try:
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return True
            
        except Exception as e:
            print(f"    ❌ Error downloading image from {image_url}: {e}")
            return False
    
    def scrape_card_images(self, delay=1, save_frequency=10):
        """Main method to scrape all card images"""
        cards_data = self.load_cards_data()
        total_cards = len(cards_data)
        
        print(f"Starting to scrape images for {total_cards} cards...")
        print(f"Will update the original JSON file: {self.json_file_path}")
        print(f"Target selector: mtg-print-image component")
        print("-" * 60)
        
        for index, card in enumerate(cards_data, 1):
            card_name = card.get('name', 'Unknown')
            card_url = card.get('card_url', '')
            set_name = card.get('set_name', 'Unknown_Set')
            
            print(f"[{index}/{total_cards}] Processing: {card_name}")
            
            if not card_url:
                print(f"  ❌ No URL found for {card_name}")
                continue
            
            # Skip if card already has image data
            if card.get('image_path') and card.get('image_url'):
                if os.path.exists(card.get('image_path')):
                    print(f"  ⏭️  Image data already exists: {card_name}")
                    continue
            
            # Create filename
            safe_card_name = self.sanitize_filename(card_name)
            safe_set_name = self.sanitize_filename(set_name)
            filename = f"{safe_card_name}_{safe_set_name}.jpg"
            file_path = os.path.join(self.output_dir, filename)
            
            # Skip if file already exists
            if os.path.exists(file_path):
                print(f"  ⏭️  Image file already exists, updating JSON: {filename}")
                card['image_path'] = file_path
                if not card.get('image_url'):
                    image_url = self.get_image_url_from_page(card_url)
                    if image_url:
                        card['image_url'] = image_url
                continue
            
            # Get image URL from the card page
            print(f"  🔍 Searching for image at: {card_url}")
            image_url = self.get_image_url_from_page(card_url)
            
            if not image_url:
                print(f"  ❌ Could not find image URL for {card_name}")
                continue
            
            print(f"  📷 Found image URL: {image_url}")
            
            # Download the image
            if self.download_image(image_url, file_path):
                print(f"  ✅ Downloaded: {filename}")
                # Update the card data with image information
                card['image_path'] = file_path
                card['image_url'] = image_url
            else:
                print(f"  ❌ Failed to download image for {card_name}")
            
            # Save progress periodically to avoid losing data
            if index % save_frequency == 0:
                self.save_cards_data(cards_data)
                print(f"  💾 Progress saved (processed {index}/{total_cards} cards)")
            
            # Be respectful to the server
            time.sleep(delay)
        
        # Final save of the updated JSON
        self.save_cards_data(cards_data)
        print(f"\n🎉 Scraping completed! Images saved to '{self.output_dir}' directory")
        print(f"📄 Original JSON file updated: {self.json_file_path}")

def main():
    # Initialize the scraper
    scraper = MTGCardImageScraper('mtg_cards_data.json', 'card_images')
    
    # Start scraping (with 1 second delay between requests, save every 10 cards)
    scraper.scrape_card_images(delay=1, save_frequency=10)

if __name__ == "__main__":
    main()