import requests
import json
import sys
import argparse
from urllib.parse import quote
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BraveSearchTool:
    def __init__(self):
        self.api_key = os.getenv('BRAVE_API_KEY')
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    def search(self, query, count=5, freshness="pw", country="US", search_lang="en"):
        """
        Search using Brave Search API
        
        Args:
            query (str): Search query
            count (int): Number of results (1-20)
            freshness (str): Time filter - pd (past day), pw (past week), pm (past month), py (past year)
            country (str): Country code for localized results
            search_lang (str): Language code
        """
        if not self.api_key:
            return {
                "error": "Brave Search API key not found. Please set BRAVE_API_KEY in your .env file",
                "success": False
            }
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": min(count, 20),  # API limit is 20
            "search_lang": search_lang,
            "country": country,
            "safesearch": "moderate",
            "freshness": freshness,
            "text_decorations": False,  # Remove HTML formatting
            "spellcheck": True
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_results(data)
            
            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Request failed: {str(e)}",
                "success": False
            }
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse response: {str(e)}",
                "success": False
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "success": False
            }
    
    def _parse_results(self, data):
        """Parse the API response and extract relevant information"""
        results = []
        
        if "web" in data and "results" in data["web"]:
            for result in data["web"]["results"]:
                parsed_result = {
                    "title": result.get("title", "").strip(),
                    "url": result.get("url", ""),
                    "description": result.get("description", "").strip(),
                    "published": result.get("age", ""),
                    "type": result.get("type", "web")
                }
                
                # Add extra info if available
                if "extra_snippets" in result:
                    parsed_result["extra_info"] = [
                        snippet.strip() for snippet in result["extra_snippets"]
                    ]
                
                results.append(parsed_result)
        
        return results
    
    def format_results_for_display(self, search_response):
        """Format search results for human-readable display"""
        if not search_response.get("success"):
            return f"❌ Search Error: {search_response.get('error', 'Unknown error')}"
        
        results = search_response.get("results", [])
        if not results:
            return "🔍 No search results found."
        
        formatted = f"🔍 Search Results for: '{search_response['query']}'\n"
        formatted += f"📊 Found {search_response['results_count']} results\n"
        formatted += "=" * 60 + "\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. 📄 {result['title']}\n"
            formatted += f"   🔗 {result['url']}\n"
            formatted += f"   📝 {result['description']}\n"
            
            if result.get('published'):
                formatted += f"   📅 {result['published']}\n"
            
            if result.get('extra_info'):
                formatted += f"   ℹ️  Additional: {'; '.join(result['extra_info'])}\n"
            
            formatted += "\n"
        
        return formatted
    
    def search_mtg_specific(self, query):
        """Search with MTG-specific optimization"""
        # Add MTG context to improve results
        mtg_query = f"Magic the Gathering MTG {query}"
        return self.search(mtg_query, count=7, freshness="pw")

def main():
    parser = argparse.ArgumentParser(description='Brave Search Tool')
    parser.add_argument('--query', '-q', required=True, help='Search query')
    parser.add_argument('--count', '-c', type=int, default=5, help='Number of results (1-20)')
    parser.add_argument('--freshness', '-f', default='pw', 
                       choices=['pd', 'pw', 'pm', 'py'], 
                       help='Time filter: pd=past day, pw=past week, pm=past month, py=past year')
    parser.add_argument('--mtg', action='store_true', help='Optimize search for MTG content')
    parser.add_argument('--json', action='store_true', help='Output raw JSON instead of formatted text')
    parser.add_argument('--country', default='US', help='Country code for localized results')
    
    args = parser.parse_args()
    
    # Initialize the search tool
    search_tool = BraveSearchTool()
    
    # Perform search
    if args.mtg:
        response = search_tool.search_mtg_specific(args.query)
    else:
        response = search_tool.search(
            query=args.query,
            count=args.count,
            freshness=args.freshness,
            country=args.country
        )
    
    # Output results
    if args.json:
        print(json.dumps(response, indent=2))
    else:
        print(search_tool.format_results_for_display(response))

if __name__ == "__main__":
    main()