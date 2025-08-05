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

def scrape_set_page(set_url, set_info, max_pages=None):
    """
    Scrapes a specific MTG set page to extract card information.
    Now handles pagination to get all cards from all pages.
    """
    print(f"\nScraping set page: {set_url}")
    all_cards_data = []
    current_url = set_url
    page_count = 0
    visited_urls = set()  # Prevent infinite loops
    
    while current_url and (max_pages is None or page_count < max_pages):
        # Prevent infinite loops
        if current_url in visited_urls:
            print(f"  Already visited {current_url}, stopping to prevent loop")
            break
        
        visited_urls.add(current_url)
        page_count += 1
        print(f"  Scraping page {page_count}: {current_url}")
        
        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {current_url}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract cards from current page
        page_cards = extract_cards_from_page(soup, set_info)
        
        if page_cards:
            all_cards_data.extend(page_cards)
            print(f"    Found {len(page_cards)} cards on page {page_count}")
        else:
            print(f"    No cards found on page {page_count}")
            # If no cards found, might be end of pagination
            break
        
        # Look for next page
        next_url = find_next_page_url(soup, current_url)
        
        if next_url and next_url != current_url:
            current_url = next_url
            print(f"    Next page found, continuing...")
            # Be polite to the server between pages
            time.sleep(2)
        else:
            print(f"    No more pages found, stopping pagination")
            break
    
    print(f"Successfully extracted {len(all_cards_data)} cards from {page_count} pages of {set_info['set_name']}")
    return all_cards_data

def extract_cards_from_page(soup, set_info):
    """
    Extract all cards from a single page.
    """
    cards_data = []
    
    # Look for table rows specifically - MTGStocks likely uses tables
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')[1:]  # Skip header row
        print(f"    Found table with {len(rows)} data rows")
        
        for row in rows:
            try:
                card_data = extract_card_info_from_row(row)
                if card_data:
                    card_data['set_id'] = set_info['set_id']
                    card_data['set_name'] = set_info['set_name']
                    cards_data.append(card_data)
            except Exception as e:
                print(f"    Error extracting card info from row: {e}")
                continue
    else:
        # Fallback to div-based structure
        print("    No table found, trying div-based extraction...")
        card_containers = soup.find_all('div', class_=re.compile(r'card|row'))
        
        for container in card_containers:
            try:
                card_data = extract_card_info(container)
                if card_data:
                    card_data['set_id'] = set_info['set_id']
                    card_data['set_name'] = set_info['set_name']
                    cards_data.append(card_data)
            except Exception as e:
                continue
    
    return cards_data

def extract_card_info_from_row(row):
    """
    Extract card information from a table row.
    """
    cells = row.find_all(['td', 'th'])
    if len(cells) < 2:
        return None
    
    card_data = {}
    
    # Try to find card name (usually in first few columns)
    for i, cell in enumerate(cells[:3]):
        link = cell.find('a')
        if link and '/prints/' in link.get('href', ''):
            card_data['name'] = link.get_text(strip=True)
            card_data['card_url'] = f"https://www.mtgstocks.com{link['href']}"
            break
        elif cell.get_text(strip=True) and not re.match(r'^\$?[\d,]+\.?\d*', cell.get_text(strip=True)):
            if not card_data.get('name'):
                card_data['name'] = cell.get_text(strip=True)
    
    # Look for price information in all cells
    for i, cell in enumerate(cells):
        cell_text = cell.get_text(strip=True)
        
        # Look for dollar amounts with more specific patterns
        price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1.23, $1,234.56
            r'(\d+(?:,\d{3})*\.\d{2})',        # 1.23, 1,234.56 (with decimals)
            r'(\d+(?:,\d{3})+)',               # 1,234 (with commas)
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, cell_text)
            if price_match:
                price_value = price_match.group(1).replace(',', '')
                try:
                    price_float = float(price_value)
                    # Only consider reasonable prices (between $0.01 and $10,000)
                    if 0.01 <= price_float <= 10000:
                        # Determine price type based on position and context
                        cell_classes = ' '.join(cell.get('class', [])).lower()
                        cell_id = cell.get('id', '').lower()
                        
                        if 'market' in cell_classes or 'market' in cell_id:
                            card_data['market_price'] = price_value
                        elif 'low' in cell_classes or 'low' in cell_id:
                            card_data['low_price'] = price_value
                        elif 'high' in cell_classes or 'high' in cell_id:
                            card_data['high_price'] = price_value
                        elif 'average' in cell_classes or 'avg' in cell_classes:
                            card_data['average_price'] = price_value
                        else:
                            # Default to main price if no specific type found
                            if not card_data.get('price'):
                                card_data['price'] = price_value
                            # Store additional prices with column index
                            price_key = f'price_col_{i}'
                            card_data[price_key] = price_value
                except ValueError:
                    continue
    
    # Look for rarity indicators
    for cell in cells:
        rarity_indicators = ['common', 'uncommon', 'rare', 'mythic', 'C', 'U', 'R', 'M']
        cell_text = cell.get_text(strip=True).lower()
        for rarity in rarity_indicators:
            if rarity.lower() in cell_text:
                card_data['rarity'] = rarity.title()
                break
        
        # Also check for rarity symbols/images
        rarity_img = cell.find('img')
        if rarity_img and rarity_img.get('alt'):
            alt_text = rarity_img.get('alt').lower()
            for rarity in rarity_indicators:
                if rarity.lower() in alt_text:
                    card_data['rarity'] = rarity.title()
                    break
    
    return card_data if card_data.get('name') else None

def extract_card_info(container):
    """
    Extract individual card information from a container element (fallback method).
    """
    card_data = {}
    
    # Try to find card name
    name_selectors = [
        container.find('a', href=re.compile(r'/prints/')),
        container.find('a', class_=re.compile(r'card|name')),
        container.find('span', class_=re.compile(r'card|name')),
        container.find('div', class_=re.compile(r'card|name'))
    ]
    
    card_name_element = next((elem for elem in name_selectors if elem), None)
    if card_name_element:
        card_data['name'] = card_name_element.get_text(strip=True)
        if card_name_element.get('href'):
            card_data['card_url'] = f"https://www.mtgstocks.com{card_name_element['href']}"
    
    # More aggressive price searching
    all_text = container.get_text()
    price_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', all_text)
    if price_matches:
        card_data['price'] = price_matches[0].replace(',', '')
    
    return card_data if card_data.get('name') else None

def debug_page_structure(set_url):
    """
    Debug function to help understand the HTML structure of a set page.
    """
    print(f"\n=== DEBUGGING PAGE STRUCTURE ===")
    print(f"URL: {set_url}")
    
    try:
        response = requests.get(set_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    if tables:
        table = tables[0]
        rows = table.find_all('tr')
        print(f"First table has {len(rows)} rows")
        
        if len(rows) > 1:
            header_row = rows[0]
            data_row = rows[1]
            
            print("Header row cells:")
            for i, cell in enumerate(header_row.find_all(['th', 'td'])):
                print(f"  {i}: '{cell.get_text(strip=True)}'")
            
            print("First data row cells:")
            for i, cell in enumerate(data_row.find_all(['th', 'td'])):
                cell_text = cell.get_text(strip=True)
                cell_classes = cell.get('class', [])
                print(f"  {i}: '{cell_text}' (classes: {cell_classes})")
    
    # Look for elements containing dollar signs (fixed deprecation warning)
    elements_with_dollars = soup.find_all(string=re.compile(r'\$\d+'))
    print(f"Found {len(elements_with_dollars)} text elements with dollar signs")
    for i, elem in enumerate(elements_with_dollars[:5]):
        print(f"  {i+1}: '{elem.strip()}'")
    
    # Look for elements that might contain prices
    price_selectors = [
        'span[class*="price"]',
        'td[class*="price"]',
        'div[class*="price"]',
        '.price',
        '[data-price]'
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector '{selector}':")
            for elem in elements[:3]:
                print(f"  - {elem.get_text(strip=True)}")

def save_cards_to_file(all_cards_data, filename='mtg_cards_data.json'):
    """
    Save all scraped card data to a JSON file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_cards_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_cards_data)} cards to {filename}")

def print_price_summary(all_cards_data):
    """
    Print a summary of price data found.
    """
    print(f"\n=== PRICE DATA SUMMARY ===")
    
    # Count cards with different types of price data
    price_fields = ['price', 'market_price', 'low_price', 'high_price', 'average_price']
    price_counts = {}
    
    for field in price_fields:
        count = sum(1 for card in all_cards_data if card.get(field))
        price_counts[field] = count
        if count > 0:
            print(f"Cards with {field}: {count}")
    
    # Show cards with any price data
    cards_with_any_price = []
    for card in all_cards_data:
        for field in price_fields:
            if card.get(field):
                cards_with_any_price.append(card)
                break
    
    print(f"Total cards with any price data: {len(cards_with_any_price)}")
    
    if cards_with_any_price:
        print(f"\nSample cards with prices:")
        for card in cards_with_any_price[:10]:
            name = card.get('name', 'Unknown')
            set_name = card.get('set_name', 'Unknown Set')
            
            # Find the best price to display
            price_display = None
            for field in price_fields:
                if card.get(field):
                    price_display = f"{field.replace('_', ' ').title()}: ${card[field]}"
                    break
            
            if not price_display:
                # Check for column-based prices
                for key, value in card.items():
                    if key.startswith('price_col_'):
                        price_display = f"Price: ${value}"
                        break
            
            print(f"  - {name} ({set_name}) - {price_display or 'No price found'}")

class MTGCardDatabase:
    def __init__(self, db_path="./mtg_cards_db"):
        """Initialize ChromaDB for MTG card storage"""
        self.db_path = db_path
        
        # Create the database directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get the collection for MTG cards
        self.collection = self.client.get_or_create_collection(
            name="mtg_cards",
            metadata={"description": "MTG card database with pricing information"}
        )
        
        print(f"ChromaDB initialized at: {db_path}")
        print(f"Current collection size: {self.collection.count()}")
    
    def normalize_card_name(self, name):
        """Improved normalization that preserves more card name structure"""
        if not name:
            return ""
        
        # Convert to lowercase and normalize spacing, but keep some punctuation
        normalized = name.lower().strip()
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        # Remove only problematic characters, keep apostrophes, hyphens, etc.
        normalized = re.sub(r'[^\w\s\'-]', '', normalized)
        return normalized
    
    def calculate_name_similarity(self, query_normalized, stored_normalized, original_stored):
        """Calculate similarity score between card names"""
        # Exact match (highest priority)
        if query_normalized == stored_normalized:
            return 100
        
        # Exact match ignoring case in original
        if query_normalized == original_stored.lower().strip():
            return 95
        
        # Query is contained in stored name
        if query_normalized in stored_normalized:
            return 80
        
        # Stored name is contained in query
        if stored_normalized in query_normalized:
            return 75
        
        # Word-by-word matching
        query_words = set(query_normalized.split())
        stored_words = set(stored_normalized.split())
        
        if not query_words or not stored_words:
            return 0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(query_words.intersection(stored_words))
        union = len(query_words.union(stored_words))
        
        if union == 0:
            return 0
        
        jaccard_score = intersection / union
        
        # Bonus for having all query words
        if query_words.issubset(stored_words):
            jaccard_score += 0.2
        
        # Convert to 0-70 scale for word matching
        return int(jaccard_score * 70)
    
    def search_card_improved(self, card_name, set_name=None, n_results=10):
        """Improved card search with better matching logic"""
        if not card_name:
            return []
        
        normalized_query = self.normalize_card_name(card_name)
        results = []
        
        try:
            # Get all cards from database
            all_cards = self.collection.get()
            
            if not all_cards['metadatas']:
                return []
            
            # Score each card based on name similarity
            scored_results = []
            
            for i, metadata in enumerate(all_cards['metadatas']):
                card_name_stored = metadata.get('name', '')
                set_name_stored = metadata.get('set_name', '')
                normalized_stored = self.normalize_card_name(card_name_stored)
                
                # Skip if set filter doesn't match
                if set_name and set_name.lower() not in set_name_stored.lower():
                    continue
                
                # Calculate similarity score
                score = self.calculate_name_similarity(normalized_query, normalized_stored, card_name_stored)
                
                if score > 0:  # Only include if there's some similarity
                    scored_results.append({
                        'id': all_cards['ids'][i],
                        'metadata': metadata,
                        'document': all_cards['documents'][i] if all_cards['documents'] else '',
                        'score': score,
                        'original_name': card_name_stored
                    })
            
            # Sort by score (higher is better) and return top results
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return scored_results[:n_results]
            
        except Exception as e:
            print(f"Error in improved search: {e}")
            return []
    
    def get_card_value_improved(self, card_name, set_name=None):
        """Improved card value lookup with better matching"""
        results = self.search_card_improved(card_name, set_name, n_results=5)
        
        if not results:
            return None
        
        # Get the best match
        best_match = results[0]
        metadata = best_match['metadata']
        
        # Extract comprehensive price information
        price_info = {
            'card_name': metadata.get('name'),
            'set_name': metadata.get('set_name'),
            'set_id': metadata.get('set_id'),
            'rarity': metadata.get('rarity'),
            'match_score': best_match['score'],
            'card_url': metadata.get('card_url'),
            'scraped_date': metadata.get('scraped_date'),
            'prices': {}
        }
        
        # Get all available prices
        price_fields = ['price', 'market_price', 'low_price', 'high_price', 'average_price']
        for field in price_fields:
            if metadata.get(field):
                try:
                    # Ensure price is a number
                    price_val = float(metadata[field])
                    price_info['prices'][field] = price_val
                except (ValueError, TypeError):
                    price_info['prices'][field] = str(metadata[field])
        
        # Get column-based prices
        for key, value in metadata.items():
            if key.startswith('price_col_'):
                try:
                    price_val = float(value)
                    price_info['prices'][key] = price_val
                except (ValueError, TypeError):
                    price_info['prices'][key] = str(value)
        
        return price_info
    
    def show_detailed_card_info(self, result):
        """Show detailed information about a specific card"""
        metadata = result['metadata']
        
        print("\n" + "="*60)
        print("DETAILED CARD INFORMATION")
        print("="*60)
        
        print(f"Name: {metadata.get('name', 'Unknown')}")
        print(f"Set: {metadata.get('set_name', 'Unknown')}")
        print(f"Set ID: {metadata.get('set_id', 'Unknown')}")
        print(f"Rarity: {metadata.get('rarity', 'Unknown')}")
        print(f"Match Score: {result['score']}/100")
        
        if metadata.get('card_url'):
            print(f"URL: {metadata['card_url']}")
        
        if metadata.get('scraped_date'):
            print(f"Data scraped: {metadata['scraped_date']}")
        
        print("\nPRICE INFORMATION:")
        print("-" * 30)
        
        # Show all available prices
        price_fields = {
            'price': 'Price',
            'market_price': 'Market Price',
            'low_price': 'Low Price',
            'high_price': 'High Price',
            'average_price': 'Average Price'
        }
        
        found_prices = False
        for field, label in price_fields.items():
            if metadata.get(field):
                try:
                    price_val = float(metadata[field])
                    print(f"{label}: ${price_val:.2f}")
                    found_prices = True
                except (ValueError, TypeError):
                    print(f"{label}: ${metadata[field]}")
                    found_prices = True
        
        # Show column-based prices
        for key, value in metadata.items():
            if key.startswith('price_col_') and value:
                col_num = key.replace('price_col_', '')
                try:
                    price_val = float(value)
                    print(f"Price (Column {col_num}): ${price_val:.2f}")
                    found_prices = True
                except (ValueError, TypeError):
                    print(f"Price (Column {col_num}): ${value}")
                    found_prices = True
        
        if not found_prices:
            print("No price information available")
        
        print("\nRAW METADATA:")
        print("-" * 30)
        for key, value in metadata.items():
            if not key.startswith('price') and key not in ['name', 'set_name', 'set_id', 'rarity', 'card_url', 'scraped_date']:
                print(f"{key}: {value}")
    
    def search_card_interactive(self):
        """Interactive card search with detailed results"""
        while True:
            print("\n" + "="*50)
            print("MTG Card Search")
            print("="*50)
            
            card_name = input("Enter card name (or 'quit' to exit): ").strip()
            
            if card_name.lower() in ['quit', 'exit', 'q']:
                break
            
            if not card_name:
                continue
            
            set_name = input("Enter set name (optional, press Enter to skip): ").strip()
            set_name = set_name if set_name else None
            
            print(f"\nSearching for: '{card_name}'" + (f" in set '{set_name}'" if set_name else ""))
            print("-" * 50)
            
            # Search for the card
            results = self.search_card_improved(card_name, set_name, n_results=10)
            
            if results:
                print(f"Found {len(results)} matches:\n")
                
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    name = metadata.get('name', 'Unknown')
                    set_name_result = metadata.get('set_name', 'Unknown Set')
                    rarity = metadata.get('rarity', 'Unknown')
                    score = result['score']
                    
                    # Get best available price
                    price_display = "No price"
                    price_fields = ['market_price', 'price', 'average_price', 'low_price', 'high_price']
                    for field in price_fields:
                        if metadata.get(field):
                            try:
                                price_val = float(metadata[field])
                                price_display = f"${price_val:.2f}"
                                break
                            except (ValueError, TypeError):
                                price_display = f"${metadata[field]}"
                                break
                    
                    # Check for additional prices
                    additional_prices = []
                    for key, value in metadata.items():
                        if key.startswith('price_col_') and value:
                            try:
                                price_val = float(value)
                                additional_prices.append(f"${price_val:.2f}")
                            except (ValueError, TypeError):
                                additional_prices.append(f"${value}")
                    
                    print(f"{i:2d}. {name}")
                    print(f"    Set: {set_name_result}")
                    print(f"    Rarity: {rarity}")
                    print(f"    Price: {price_display}")
                    if additional_prices:
                        print(f"    Other prices: {', '.join(additional_prices)}")
                    print(f"    Match score: {score}/100")
                    
                    if metadata.get('card_url'):
                        print(f"    URL: {metadata['card_url']}")
                    print()
                
                # Ask if user wants detailed info on a specific card
                try:
                    choice = input("Enter number for detailed info (or press Enter to continue): ").strip()
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(results):
                            self.show_detailed_card_info(results[idx])
                except ValueError:
                    pass
                    
            else:
                print("No matches found.")
                print("\nTips:")
                print("- Try a shorter or partial name")
                print("- Check spelling")
                print("- Try without set name")

    def create_card_document(self, card_data):
        """Create a searchable document from card data"""
        name = card_data.get('name', '')
        set_name = card_data.get('set_name', '')
        rarity = card_data.get('rarity', '')
        
        # Create a comprehensive text document for embedding
        document_parts = [
            f"Card Name: {name}",
            f"Set: {set_name}",
        ]
        
        if rarity:
            document_parts.append(f"Rarity: {rarity}")
        
        # Add any additional descriptive information
        if card_data.get('type'):
            document_parts.append(f"Type: {card_data['type']}")
        
        return " | ".join(document_parts)
    
    def add_cards_to_database(self, cards_data):
        """Add multiple cards to the ChromaDB database"""
        if not cards_data:
            print("No cards to add to database")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for card in cards_data:
            if not card.get('name'):
                continue
            
            # Create document for embedding
            document = self.create_card_document(card)
            documents.append(document)
            
            # Prepare metadata (ChromaDB metadata must be simple types)
            metadata = {
                'name': card.get('name', ''),
                'normalized_name': self.normalize_card_name(card.get('name', '')),
                'set_name': card.get('set_name', ''),
                'set_id': str(card.get('set_id', '')),
                'rarity': card.get('rarity', ''),
                'scraped_date': datetime.now().isoformat(),
            }
            
            # Add price information
            price_fields = ['price', 'market_price', 'low_price', 'high_price', 'average_price']
            for field in price_fields:
                if card.get(field):
                    try:
                        # Convert price to float for storage
                        price_value = float(str(card[field]).replace(',', '').replace('$', ''))
                        metadata[field] = price_value
                    except (ValueError, TypeError):
                        metadata[field] = str(card[field])
            
            # Add any column-based prices
            for key, value in card.items():
                if key.startswith('price_col_'):
                    try:
                        price_value = float(str(value).replace(',', '').replace('$', ''))
                        metadata[key] = price_value
                    except (ValueError, TypeError):
                        metadata[key] = str(value)
            
            # Add card URL if available
            if card.get('card_url'):
                metadata['card_url'] = card['card_url']
            
            metadatas.append(metadata)
            
            # Create unique ID
            card_id = f"{card.get('set_id', 'unknown')}_{self.normalize_card_name(card.get('name', ''))}"
            card_id = re.sub(r'[^\w]', '_', card_id)
            ids.append(f"{card_id}_{uuid.uuid4().hex[:8]}")
        
        if documents:
            try:
                # Add to ChromaDB
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Successfully added {len(documents)} cards to ChromaDB")
            except Exception as e:
                print(f"Error adding cards to database: {e}")
                # Try adding in smaller batches
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    try:
                        batch_docs = documents[i:i+batch_size]
                        batch_meta = metadatas[i:i+batch_size]
                        batch_ids = ids[i:i+batch_size]
                        
                        self.collection.add(
                            documents=batch_docs,
                            metadatas=batch_meta,
                            ids=batch_ids
                        )
                        print(f"Added batch {i//batch_size + 1}: {len(batch_docs)} cards")
                    except Exception as batch_error:
                        print(f"Error adding batch {i//batch_size + 1}: {batch_error}")
    
    def search_card(self, card_name, n_results=5):
        """Search for a card by name"""
        query = f"Card Name: {card_name}"
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return self.format_search_results(results)
        except Exception as e:
            print(f"Error searching for card: {e}")
            return []
    
    def search_card_fuzzy(self, card_name, n_results=10):
        """Search for cards with fuzzy matching"""
        normalized_name = self.normalize_card_name(card_name)
        
        try:
            # First try exact embedding search
            query = f"Card Name: {card_name}"
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Also try metadata filtering for normalized names
            all_cards = self.collection.get()
            fuzzy_matches = []
            
            for i, metadata in enumerate(all_cards['metadatas']):
                stored_normalized = metadata.get('normalized_name', '')
                if stored_normalized and normalized_name in stored_normalized:
                    fuzzy_matches.append({
                        'id': all_cards['ids'][i],
                        'metadata': metadata,
                        'document': all_cards['documents'][i] if all_cards['documents'] else '',
                        'distance': 0.5  # Assign a moderate distance for fuzzy matches
                    })
            
            # Combine and deduplicate results
            combined_results = self.format_search_results(results)
            
            for match in fuzzy_matches[:n_results]:
                if not any(r['id'] == match['id'] for r in combined_results):
                    combined_results.append(match)
            
            return combined_results[:n_results]
            
        except Exception as e:
            print(f"Error in fuzzy search: {e}")
            return []
    
    def format_search_results(self, results):
        """Format ChromaDB results into a readable format"""
        formatted_results = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted_results
        
        for i in range(len(results['ids'][0])):
            result = {
                'id': results['ids'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if results.get('distances') else None,
                'document': results['documents'][0][i] if results.get('documents') else ''
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def get_card_value(self, card_name, set_name=None):
        """Get the current value of a card"""
        results = self.search_card_fuzzy(card_name)
        
        if set_name:
            # Filter by set if specified
            results = [r for r in results if set_name.lower() in r['metadata'].get('set_name', '').lower()]
        
        if not results:
            return None
        
        best_match = results[0]
        metadata = best_match['metadata']
        
        # Extract price information
        price_info = {
            'card_name': metadata.get('name'),
            'set_name': metadata.get('set_name'),
            'rarity': metadata.get('rarity'),
            'prices': {}
        }
        
        # Get all available prices
        price_fields = ['price', 'market_price', 'low_price', 'high_price', 'average_price']
        for field in price_fields:
            if metadata.get(field):
                price_info['prices'][field] = metadata[field]
        
        # Get column-based prices
        for key, value in metadata.items():
            if key.startswith('price_col_'):
                price_info['prices'][key] = value
        
        return price_info
    
    def print_database_stats(self):
        """Print statistics about the database"""
        count = self.collection.count()
        print(f"\n=== MTG Card Database Statistics ===")
        print(f"Total cards in database: {count}")
        
        if count > 0:
            # Get sample of cards to show sets and price coverage
            sample = self.collection.get(limit=min(1000, count))
            
            sets = set()
            cards_with_prices = 0
            
            for metadata in sample['metadatas']:
                if metadata.get('set_name'):
                    sets.add(metadata['set_name'])
                
                # Check if card has any price information
                price_fields = ['price', 'market_price', 'low_price', 'high_price', 'average_price']
                if any(metadata.get(field) for field in price_fields):
                    cards_with_prices += 1
            
            print(f"Number of sets: {len(sets)}")
            print(f"Cards with price data: {cards_with_prices}/{len(sample['metadatas'])}")
            
            if sets:
                print(f"Sample sets: {', '.join(list(sets)[:10])}")

def load_scraped_set_ids(progress_file='scraped_sets.json'):
    """Load the set IDs that have already been scraped from a progress file."""
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            try:
                return set(json.load(f))
            except Exception:
                return set()
    return set()

def save_scraped_set_id(set_id, progress_file='scraped_sets.json'):
    """Append a set ID to the progress file after scraping."""
    scraped = load_scraped_set_ids(progress_file)
    scraped.add(str(set_id))
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(scraped, key=int), f, indent=2)

def main():
    """Main function to scrape MTGStocks and populate ChromaDB, with resume support."""
    db = MTGCardDatabase()
    all_sets_info = get_all_mtgstocks_set_urls()
    if not all_sets_info:
        print("No sets found to scrape.")
        return
    print(f"\nFound {len(all_sets_info)} sets.")

    # Load progress
    scraped_set_ids = load_scraped_set_ids()
    print(f"Sets already scraped: {sorted(scraped_set_ids, key=int)}")

    # Filter sets to scrape
    sets_to_scrape = [s for s in all_sets_info if s['set_id'] not in scraped_set_ids]
    print(f"Sets left to scrape: {len(sets_to_scrape)}")

    if not sets_to_scrape:
        print("All sets have already been scraped.")
        return

    try:
        num_sets = int(input(f"How many sets would you like to scrape? (1-{len(sets_to_scrape)}): "))
        num_sets = min(num_sets, len(sets_to_scrape))
    except ValueError:
        num_sets = 1
        print(f"Invalid input. Defaulting to {num_sets} set.")

    print(f"\nScraping {num_sets} sets and storing in ChromaDB...")
    total_cards_added = 0

    # Load or initialize card data file
    card_data_json = 'mtg_cards_data.json'
    if os.path.exists(card_data_json):
        with open(card_data_json, 'r', encoding='utf-8') as f:
            try:
                all_cards_json = json.load(f)
            except Exception:
                all_cards_json = []
    else:
        all_cards_json = []

    for i, set_info in enumerate(sets_to_scrape[:num_sets]):
        print(f"\n--- Processing set {i+1}/{num_sets}: {set_info['set_name']} (ID: {set_info['set_id']}) ---")
        cards_data = scrape_set_page(set_info['full_url'], set_info)
        if cards_data:
            print(f"Scraped {len(cards_data)} cards from {set_info['set_name']}")
            db.add_cards_to_database(cards_data)
            total_cards_added += len(cards_data)
            print(f"Added {len(cards_data)} cards to database")
            save_scraped_set_id(set_info['set_id'])  # Save progress
            # Save to JSON as well
            all_cards_json.extend(cards_data)
            with open(card_data_json, 'w', encoding='utf-8') as f:
                json.dump(all_cards_json, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(all_cards_json)} total cards to {card_data_json}")
        else:
            print(f"No cards found for {set_info['set_name']}")
        if i < num_sets - 1:
            print("Waiting 3 seconds before next request...")
            time.sleep(3)

    print(f"\n=== SCRAPING COMPLETE ===")
    print(f"Total cards added to database: {total_cards_added}")

    # Print missing sets
    all_set_ids = set(s['set_id'] for s in all_sets_info)
    scraped_set_ids = load_scraped_set_ids()
    missing_set_ids = sorted(all_set_ids - scraped_set_ids, key=int)
    print(f"Sets not scraped: {missing_set_ids}")
    with open('missing_sets.json', 'w', encoding='utf-8') as f:
        json.dump(missing_set_ids, f, indent=2)
    print("Missing set IDs saved to missing_sets.json")

    db.print_database_stats()
    print(f"\n=== TESTING SEARCH FUNCTIONALITY ===")
    test_search_improved(db)

def test_search_improved(db):
    """Improved test search functionality"""
    print("\n=== TESTING IMPROVED SEARCH FUNCTIONALITY ===")
    
    # Run interactive search
    db.search_card_interactive()
    
    # Also test programmatic search
    print("\n=== PROGRAMMATIC SEARCH EXAMPLES ===")
    
    test_cards = ["Lightning Bolt", "Black Lotus", "Jace", "Serra Angel"]
    
    for card_name in test_cards:
        print(f"\nTesting search for: '{card_name}'")
        value_info = db.get_card_value_improved(card_name)
        
        if value_info:
            print(f"Found: {value_info['card_name']} ({value_info['set_name']})")
            print(f"Match score: {value_info['match_score']}/100")
            if value_info['prices']:
                best_price = next(iter(value_info['prices'].values()))
                print(f"Price: ${best_price}")
            else:
                print("No price available")
        else:
            print("Not found")

def get_card_price(card_name, set_name=None):
    db = MTGCardDatabase()
    return db.get_card_value_improved(card_name, set_name)

if __name__ == "__main__":
    main()