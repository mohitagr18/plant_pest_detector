# mcp_server/agri_tools.py
# All agricultural tools in one MCP server for Gemini to discover and use

import os
import sys
import requests
import re
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp.server.fastmcp import FastMCP
from src.location_service import LocationService

# Initialize FastMCP server with all tools
mcp = FastMCP("Agricultural Assistant Tools")

# Initialize services
location_service = LocationService()


# ============================================================================
# WEATHER TOOL
# ============================================================================

@mcp.tool()
def get_weather(zipcode: str) -> dict:
    """
    Get current weather conditions and 3-day forecast for a US zip code.
    
    Args:
        zipcode: 5-digit US zip code
    
    Returns:
        Weather data including temperature, wind, conditions, and forecast
    """
    return location_service.get_weather_data(zipcode)


# ============================================================================
# SOIL TOOL
# ============================================================================

@mcp.tool()
def get_soil_type(zipcode: str) -> dict:
    """
    Get soil type and properties for a US zip code from USDA data.
    
    Args:
        zipcode: 5-digit US zip code
    
    Returns:
        Soil data including texture, drainage, pH, composition
    """
    return location_service.get_soil_data(zipcode)


# ============================================================================
# AMAZON PRODUCT SEARCH TOOL
# ============================================================================

class SerperProductSearch:
    """Product search using Serper API"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found")
        
        self.base_url = "https://google.serper.dev/search"
    
    def search_products(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search for Amazon products"""
        try:
            search_query = f"site:amazon.com {query}"
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": search_query,
                "num": max_results + 2,
                "gl": "us"
            }
            
            print(f"🔍 Searching Amazon via Serper: {query}")
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(data, query, max_results)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return [{
                "name": f"Search results for: {query}",
                "url": f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
            }]
    
    def _validate_amazon_url(self, url: str) -> bool:
        """Check if Amazon URL is valid"""
        if not url or url == "#":
            return False
        
        if "/dp/" in url:
            return bool(re.search(r'/dp/([A-Z0-9]{10})', url))
        elif "/gp/product/" in url:
            return bool(re.search(r'/gp/product/([A-Z0-9]{10})', url))
        
        if "/s?" in url and "k=" in url:
            return True
        
        return False
    
    def _parse_response(self, data: dict, original_query: str, max_results: int) -> List[Dict]:
        """Parse Serper response"""
        products = []
        
        try:
            organic_results = data.get("organic", [])
            
            if not organic_results:
                return []
            
            for item in organic_results:
                if len(products) >= max_results:
                    break
                
                title = item.get("title", "Unknown Product")
                link = item.get("link", "#")
                
                if not self._validate_amazon_url(link):
                    continue
                
                products.append({
                    "name": title,
                    "url": link
                })
        
        except Exception as e:
            print(f"❌ Parse error: {e}")
        
        if not products:
            products = [{
                "name": f"View search results for: {original_query}",
                "url": f"https://www.amazon.com/s?k={original_query.replace(' ', '+')}"
            }]
        
        return products


@mcp.tool()
def search_amazon_products(query: str, max_results: int = 3) -> List[Dict]:
    """
    Search for Amazon products related to agricultural pest/disease treatment.
    
    Args:
        query: Search query for products (e.g., "organic Bt spray", "neem oil concentrate")
        max_results: Number of results to return (default 3)
    
    Returns:
        List of products with name and Amazon URL
    """
    client = SerperProductSearch()
    return client.search_products(query, max_results)


# ============================================================================
# LOCATION CONTEXT TOOL (Combined Weather + Soil)
# ============================================================================

@mcp.tool()
def get_location_context(zipcode: str) -> dict:
    """
    Get complete location context including weather and soil data for a US zip code.
    
    Args:
        zipcode: 5-digit US zip code
    
    Returns:
        Combined weather and soil data for the location
    """
    return location_service.get_location_context(zipcode)
