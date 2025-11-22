"""
Querido Diário API Client.

This module provides functions to interact with the Querido Diário API,
which provides access to official gazettes from Brazilian municipalities.
API Documentation: https://queridodiario.ok.org.br/api/docs
"""

import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.logging_config import logger


BASE_URL = "https://queridodiario.ok.org.br/api"
TIMEOUT = 30.0


async def search_gazette(city: str, query: str, limit: int = 5) -> List[Dict]:
    """
    Search for content in official gazettes of a specific city.
    
    Args:
        city: City name (e.g., "São Paulo", "Rio de Janeiro")
        query: Search query (e.g., "merenda escolar", "transporte")
        limit: Maximum number of results to return
        
    Returns:
        List of gazette excerpts containing the search term
        
    Example:
        >>> results = await search_gazette(city="São Paulo", query="merenda escolar")
        >>> for r in results:
        ...     print(f"{r['date']}: {r['excerpt']}")
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # First, we need to get the city's territory_id
            territory_id = await _get_territory_id(city, client)
            
            if not territory_id:
                logger.warning(f"City '{city}' not found in Querido Diário database")
                return []
            
            # Search in gazettes
            params = {
                "territory_ids": territory_id,
                "querystring": query,
                "size": limit,
                "sort_by": "descending_date"
            }
            
            response = await client.get(f"{BASE_URL}/gazettes", params=params)
            response.raise_for_status()
            
            data = response.json()
            gazettes = data.get("gazettes", [])
            
            result = []
            for gaz in gazettes:
                # Get excerpt with the search term
                excerpt = await _get_excerpt(gaz.get("url"), query, client)
                
                result.append({
                    "date": gaz.get("date"),
                    "city": city,
                    "territory_id": territory_id,
                    "edition": gaz.get("edition_number"),
                    "url": gaz.get("url"),
                    "excerpt": excerpt,
                    "file_url": gaz.get("file_url")
                })
            
            logger.info(f"Found {len(result)} gazette entries for '{query}' in {city}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error searching gazettes: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching gazettes: {e}", exc_info=True)
        return []


async def _get_territory_id(city_name: str, client: httpx.AsyncClient) -> Optional[str]:
    """
    Get the territory ID for a city name.
    
    Args:
        city_name: Name of the city
        client: HTTP client instance
        
    Returns:
        Territory ID (IBGE code) or None if not found
    """
    try:
        # Search for the city
        response = await client.get(f"{BASE_URL}/cities/{city_name}")
        
        if response.status_code == 200:
            data = response.json()
            # The API returns the city data directly
            return data.get("territory_id")
        else:
            # Try searching in the cities list
            response = await client.get(f"{BASE_URL}/cities")
            response.raise_for_status()
            
            cities = response.json()
            
            # Normalize city name for comparison
            normalized_search = city_name.lower().strip()
            
            for city in cities:
                city_full_name = city.get("territory_name", "").lower()
                if normalized_search in city_full_name:
                    return city.get("territory_id")
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting territory ID for {city_name}: {e}")
        return None


async def _get_excerpt(gazette_url: str, query: str, client: httpx.AsyncClient, context_chars: int = 200) -> str:
    """
    Get an excerpt from the gazette text containing the search query.
    
    Args:
        gazette_url: URL to the gazette text
        query: Search term
        context_chars: Number of characters to show around the match
        client: HTTP client instance
        
    Returns:
        Text excerpt or empty string if not found
    """
    try:
        if not gazette_url:
            return ""
        
        response = await client.get(gazette_url)
        response.raise_for_status()
        
        text = response.text
        
        # Find the query in the text (case-insensitive)
        query_lower = query.lower()
        text_lower = text.lower()
        
        index = text_lower.find(query_lower)
        
        if index == -1:
            # Query not found, return beginning of text
            return text[:context_chars] + "..."
        
        # Extract excerpt with context
        start = max(0, index - context_chars)
        end = min(len(text), index + len(query) + context_chars)
        
        excerpt = text[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
        
        return excerpt.strip()
        
    except Exception as e:
        logger.error(f"Error extracting excerpt: {e}")
        return ""


async def get_recent_gazettes(city: str, days: int = 7, limit: int = 5) -> List[Dict]:
    """
    Get recent gazettes from a city.
    
    Args:
        city: City name
        days: Number of days to look back
        limit: Maximum number of results
        
    Returns:
        List of recent gazettes
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            territory_id = await _get_territory_id(city, client)
            
            if not territory_id:
                logger.warning(f"City '{city}' not found")
                return []
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                "territory_ids": territory_id,
                "since": start_date.strftime("%Y-%m-%d"),
                "until": end_date.strftime("%Y-%m-%d"),
                "size": limit,
                "sort_by": "descending_date"
            }
            
            response = await client.get(f"{BASE_URL}/gazettes", params=params)
            response.raise_for_status()
            
            data = response.json()
            gazettes = data.get("gazettes", [])
            
            result = []
            for gaz in gazettes:
                result.append({
                    "date": gaz.get("date"),
                    "city": city,
                    "territory_id": territory_id,
                    "edition": gaz.get("edition_number"),
                    "url": gaz.get("url"),
                    "file_url": gaz.get("file_url")
                })
            
            logger.info(f"Found {len(result)} recent gazettes for {city}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching recent gazettes: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching recent gazettes: {e}", exc_info=True)
        return []
