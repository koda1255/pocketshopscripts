import requests
from bs4 import BeautifulSoup
import re
import time
import json
from urllib.parse import urljoin, urlparse, parse_qs
import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime
import os
import hashlib
from PIL import Image
import io

def get_all_mtgstocks_set_urls():
    """
    Scrapes MTGStocks' /sets page to extract URLs for all individual sets,
    along with their set_id and set_name_slug.
    """
    base_url = "https://www.mtgstocks.com"
    sets_listing_url = f"{base_url}/sets"
    set_data = []

    print(f"Fetching: {sets_listing_url}")
    try:
        response = requests.get(sets_listing_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the sets listing page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    set_links_container = soup.find('div', class_='col-12')
    if not set_links_container:
        print("Could not find the container for set links. Check the HTML structure.")
        all_links = soup.find_all('a', href=re.compile(r'/sets/\d+-.+'))
    else:
        all_links = set_links_container.find_all('a', href=re.compile(r'/sets/\d+-.+'))

    if not all_links:
        print("No set links found. Check the HTML structure and CSS selectors.")
        return []

    for link in all_links:
        href = link.get('href')
        if href and href.startswith('/sets/'):
            match = re.match(r'/sets/(\d+)-(.+)', href)
            if match:
                set_id = match.group(1)
                set_name_slug = match.group(2)
                full_set_url = f"{base_url}{href}"
                set_name = link.get_text(strip=True)
                set_data.append({
                    'set_id': set_id,
                    'set_name_slug': set_name_slug,
                    'full_url': full_set_url,
                    'set_name': set_name
                })
            else:
                print(f"Could not parse href: {href}")
    return set_data

def download_image(image_url, save_path, max_retries=3):
    """
    Download an image from a URL and save it to the specified path.
    Returns True if successful, False otherwise.
    """
    if not image_url:
        return False
    
    # Make sure the image URL is absolute
    if image_url.startswith('//'):
        image_url = 'https:' + image_url
    elif image_url.startswith('/'):
        image_url = 'https://www.mtgstocks.com' + image_url
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Verify it's actually an image
            try:
                img = Image.open(io.BytesIO(response.content))
                img.verify()  # Verify it's a valid image
            except Exception as e:
                print(f"Invalid image data from {image_url}: {e}")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"    Downloaded image: {os.path.basename(save_path)}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"    Attempt {attempt + 1} failed to download {image_url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
            
        except Exception as e:
            print(f"    Error saving image {image_url}: {e}")
            return False
    
    return False

def extract_card_image_url(row_or_container):
    """
    Extract card image URL from a table row or container element.
    """
    # Look for img tags in the row/container
    img_tags = row_or_container.find_all('img')
    
    for img in img_tags:
        src = img.get('src')
        data_src = img.get('data-src')  # Lazy loading
        
        # Prefer data-src if available (lazy loading)
        image_url = data_src or src
        
        if image_url:
            # Filter out non-card images (icons, logos, etc.)
            if any(keyword in image_url.lower() for keyword in ['card', 'print', 'image']):
                return image_url
            # If no specific keywords, but it looks like a card image URL
            elif re.search(r'\.(jpg|jpeg|png|webp)', image_url.lower()):
                # Exclude obvious non-card images
                if not any(keyword in image_url.lower() for keyword in ['icon', 'logo', 'symbol', 'mana']):
                    return image_url
    
    # Also check for background images in style attributes
    elements_with_style = row_or_container.find_all(attrs={'style': True})
    for element in elements_with_style:
        style = element.get('style', '')
        bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
        if bg_match:
            return bg_match.group(1)
    
    return None

def generate_image_filename(card_name, set_name, set_id, image_url):
    """
    Generate a consistent filename for the card image.
    """
    # Clean the card name for filename
    clean_name = re.sub(r'[^\w\s-]', '', card_name).strip()
    clean_name = re.sub(r'\s+', '_', clean_name)
    
    # Clean set name
    clean_set = re.sub(r'[^\w\s-]', '', set_name).strip()
    clean_set = re.sub(r'\s+', '_', clean_set)
    
    # Get file extension from URL
    parsed_url = urlparse(image_url)
    path = parsed_url.path
    ext = os.path.splitext(path)[1]
    if not ext:
        ext = '.jpg'  # Default extension
    
    # Create filename: setid_setname_cardname.ext
    filename = f"{set_id}_{clean_set}_{clean_name}{ext}"
    
    # Ensure filename isn't too long
    if len(filename) > 200:
        # Create a hash of the card name if too long
        name_hash = hashlib.md5(card_name.encode()).hexdigest()[:8]
        filename = f"{set_id}_{clean_set}_{name_hash}{ext}"
    
    return filename

def debug_pagination_structure(soup):
    """
    Debug function to understand the exact pagination structure
    """
    print(f"\n=== DETAILED PAGINATION DEBUG ===")
    
    # Find all pagination-related elements
    pagination_elements = soup.find_all(['ul', 'div', 'nav'], class_=re.compile(r'pag', re.I))
    print(f"Found {len(pagination_elements)} pagination containers")
    
    for i, container in enumerate(pagination_elements):
        print(f"\nPagination container {i+1}:")
        print(f"  Tag: {container.name}")
        print(f"  Classes: {container.get('class', [])}")
        print(f"  HTML: {str(container)[:200]}...")
        
        # Find all page items
        page_items = container.find_all('li', class_='page-item')
        print(f"  Found {len(page_items)} page-item elements:")
        
        for j, item in enumerate(page_items):
            button = item.find('button', class_='page-link')
            link = item.find('a', class_='page-link')
            
            if button:
                text = button.get_text(strip=True)
                classes = item.get('class', [])
                print(f"    Item {j+1}: BUTTON '{text}' (li classes: {classes})")
            elif link:
                text = link.get_text(strip=True)
                href = link.get('href', 'No href')
                classes = item.get('class', [])
                print(f"    Item {j+1}: LINK '{text}' -> {href} (li classes: {classes})")
            else:
                text = item.get_text(strip=True)
                classes = item.get('class', [])
                print(f"    Item {j+1}: OTHER '{text}' (li classes: {classes})")
    
    # Also look for any elements that might indicate total pages or results
    total_indicators = soup.find_all(string=re.compile(r'(\d+)\s*(of|/)\s*(\d+)|total|results|showing', re.I))
    if total_indicators:
        print(f"\nPossible total/results indicators:")
        for indicator in total_indicators[:5]:
            print(f"  '{indicator.strip()}'")

def find_next_page_url(soup, current_url):
    """
    Find the URL for the next page of results.
    Enhanced to better handle MTGStocks pagination structure.
    """
    base_url = "https://www.mtgstocks.com"
    
    # Debug the pagination structure
    debug_pagination_structure(soup)
    
    # First, try to find the current page number
    current_page = 1
    
    # Look for active page indicator in pagination
    page_items = soup.find_all('li', class_='page-item')
    
    for item in page_items:
        if 'active' in item.get('class', []):
            button = item.find('button', class_='page-link')
            link = item.find('a', class_='page-link')
            
            if button:
                text = button.get_text(strip=True)
                if text.isdigit():
                    current_page = int(text)
                    break
            elif link:
                text = link.get_text(strip=True)
                if text.isdigit():
                    current_page = int(text)
                    break
    
    # Also check URL for page parameter
    try:
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        if 'page' in query_params:
            current_page = int(query_params['page'][0])
    except:
        pass
    
    print(f"    Current page detected as: {current_page}")
    
    # Find all page numbers to determine max page
    max_page = current_page
    page_numbers = []
    
    for item in page_items:
        button = item.find('button', class_='page-link')
        link = item.find('a', class_='page-link')
        
        element = button or link
        if element:
            text = element.get_text(strip=True)
            if text.isdigit():
                page_num = int(text)
                page_numbers.append(page_num)
                max_page = max(max_page, page_num)
    
    print(f"    Page numbers found: {sorted(page_numbers)}")
    print(f"    Max page detected: {max_page}")
    
    # Check if there's a "Next" button that's not disabled
    for item in page_items:
        button = item.find('button', class_='page-link')
        if button:
            text = button.get_text(strip=True).lower()
            if 'next' in text:
                item_classes = item.get('class', [])
                button_classes = button.get('class', [])
                
                print(f"    Found Next button - item classes: {item_classes}, button classes: {button_classes}")
                
                # Check if disabled
                if 'disabled' not in item_classes and 'disabled' not in button_classes:
                    print(f"    Next button is enabled")
                    # Since it's a button (JavaScript), we need to construct the URL
                    next_page = current_page + 1
                    
                    if next_page <= max_page:
                        # Construct next page URL
                        if 'page=' in current_url:
                            next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)
                        else:
                            separator = '&' if '?' in current_url else '?'
                            next_url = f"{current_url}{separator}page={next_page}"
                        
                        print(f"    Constructed next page URL: {next_url}")
                        return next_url
                    else:
                        print(f"    Next page ({next_page}) would exceed max page ({max_page})")
                        return None
                else:
                    print(f"    Next button is disabled")
                    return None
    
    # If no Next button found, try to construct URL based on page numbers
    if current_page < max_page:
        next_page = current_page + 1
        print(f"    No Next button found, but current page ({current_page}) < max page ({max_page})")
        
        # Try to find a link to the next page number
        for item in page_items:
            link = item.find('a', class_='page-link')
            if link:
                text = link.get_text(strip=True)
                if text == str(next_page):
                    next_url = urljoin(base_url, link.get('href'))
                    print(f"    Found link to page {next_page}: {next_url}")
                    return next_url
        
        # Construct URL manually
        if 'page=' in current_url:
            next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)
        else:
            separator = '&' if '?' in current_url else '?'
            next_url = f"{current_url}{separator}page={next_page}"
        
        print(f"    Constructed next page URL: {next_url}")
        return next_url
    
    print(f"    No next page available")
    return None

def load_progress(progress_file):
    """
    Load progress from a JSON file.
    """
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_progress(progress, progress_file):
    """
    Save progress to a JSON file.
    """
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)

def extract_mtgstocks_card_id(card_url):
    """
    Extracts the MTGStocks card ID from a card URL (e.g., /prints/12345 or /cards/12345).
    """
    match = re.search(r'/cards/(\d+)', card_url)
    if match:
        return match.group(1)
    match = re.search(r'/prints/(\d+)', card_url)
    if match:
        return match.group(1)
    return None

def scrape_set_page(set_url, set_info, max_pages=None, download_images=True, images_dir="./card_images", progress_file="progress.json"):
    """
    Scrapes a specific MTG set page to extract card information.
    Now handles pagination to get all cards from all pages and downloads images.
    Saves progress and can resume.
    """
    print(f"\nScraping set page: {set_url}")
    all_cards_data = []
    current_url = set_url
    progress = load_progress(progress_file)
    set_id = set_info.get('set_id')
    set_progress = progress.get(set_id, {'last_page': 1, 'cards': []})
    last_page = set_progress.get('last_page', 1)
    scraped_card_ids = set(card['mtgstocks_id'] for card in set_progress.get('cards', []))
    page_num = last_page
    while current_url:
        print(f"Processing page {page_num}...")
        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {current_url}: {e}")
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all card rows/containers
        card_rows = soup.find_all('tr', class_=re.compile(r'card-row|card', re.I))
        for row in card_rows:
            card_link = None
            for a in row.find_all('a'):
                href = a.get('href', '')
                if re.match(r'/cards/\d+', href):
                    card_link = a
                    break
            if not card_link:
                continue
            card_url = card_link.get('href', '')
            mtgstocks_id = extract_mtgstocks_card_id(card_url)
            card_name = card_link.get_text(strip=True)
            if mtgstocks_id in scraped_card_ids:
                continue  # Already scraped
            image_url = extract_card_image_url(row)
            filename = generate_image_filename(card_name, set_info['set_name'], set_info['set_id'], image_url) if image_url else None
            if download_images and image_url and filename:
                download_image(image_url, os.path.join(images_dir, filename))
            card_data = {
                'mtgstocks_id': mtgstocks_id,
                'card_name': card_name,
                'image_url': image_url,
                'image_filename': filename
            }
            set_progress['cards'].append(card_data)
            scraped_card_ids.add(mtgstocks_id)
            save_progress(progress, progress_file)
        # Save page progress
        set_progress['last_page'] = page_num
        progress[set_id] = set_progress
        save_progress(progress, progress_file)
        # Find next page URL
        next_url = find_next_page_url(soup, current_url)
        if not next_url or (max_pages and page_num >= max_pages):
            break
        current_url = next_url
        page_num += 1
    print(f"Finished scraping set {set_info['set_name']} (ID: {set_id})")
    return set_progress['cards']
