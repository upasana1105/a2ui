import urllib.parse
import googlemaps
import logging
import binascii
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Global cache to map place_id -> photo_reference to avoid long URLs in UI
IMAGE_CACHE = {}

def search_properties(query: str, location: str) -> List[Dict[str, Any]]:
    """
    Search for properties or real estate listings using Google Maps Places API.
    """
    logger.info(f"[CACHE_DIAG] Current process PID: {os.getpid()}")
    logger.info(f"[CACHE_DIAG] IMAGE_CACHE size on entry: {len(IMAGE_CACHE)}")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in environment.")
        return []

    try:
        logger.info(f"Calling search_properties with query='{query}' and location='{location}'")
        gmaps = googlemaps.Client(key=api_key)
        
        # We want to find actual listings, not real estate agencies.
        # Adding 'address' to the search query often helps Google Maps find specific residential properties.
        # Use more specific residential keywords
        full_query = f"{query} in {location} residential property single family home"
        logger.info(f"Full query for Places API: {full_query}")
        
        places_result = gmaps.places(query=full_query)
        
        results = []
        # Aggressive filter for commercial real estate entities
        avoid_keywords = [
            "realty", "agency", "real estate", "broker", "office", 
            "management", "apartment", "complex", "corporate", "builders",
            "development", "advisors", "properties", "mortgage", "lending",
            "title", "escrow", "associates", "partners", "group", "team"
        ]
        
        for place in places_result.get('results', []):
            name = place.get('name', '').lower()
            # Unconditional skip if it contains multiple suspicious keywords
            if any(kw in name for kw in avoid_keywords):
                # If it has "Real Estate" or "Realty" or "Broker", it's almost certainly a company.
                if any(kw in name for kw in ["real estate", "realty", "broker", "agency", "management"]):
                    continue
                # If we have some results, be even more aggressive
                if len(results) >= 1:
                    continue
                
            logger.debug(f"Processing place: {place.get('name')}")
            
            # OPTIMIZATION: Avoid sequential 'gmaps.place' calls for details.
            # We can construct the public URL using place_id directly.
            place_id = place.get('place_id')
            public_url = f"https://www.google.com/maps/search/?api=1&query={place.get('formatted_address')}&query_place_id={place_id}"
            
            photo_url = None
            if place.get("photos"):
                photo_ref = place.get("photos")[0].get("photo_reference")
                IMAGE_CACHE[place_id] = photo_ref
                logger.info(f"[CACHE_DIAG] Cached photo_ref for {place_id}. Cache size: {len(IMAGE_CACHE)}")
                base_url = os.getenv("BASE_URL", "http://localhost:10003")
                encoded_name = urllib.parse.quote(place.get('name', 'residential house'))
                photo_url = f"{base_url}/proxy-image?id={place_id}&desc={encoded_name}"

            # Fallback if no photo found in Places API
            if not photo_url:
                # Use property name or id to generate a unique but house-relevant image
                seed = place_id or place.get('name', 'house').replace(' ', '_')
                # LoremFlickr with house/interior keywords and a 'lock' for consistency
                photo_url = f"https://loremflickr.com/800/600/house,interior,home/all?lock={hash(seed) % 10000}"

            results.append({
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "rating": f"Rating: {place.get('rating')}" if place.get("rating") else "New listing",
                "place_id": place_id,
                "publicUrl": public_url,
                "imageUrl": photo_url
            })
            
            if len(results) >= 6: # Cap at 6 for speed
                break
        
        logger.info(f"Returning {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error calling Google Maps API: {e}", exc_info=True)
        return []

def search_realtor_listings(location: str, query: str = "") -> List[Dict[str, Any]]:
    """
    Search for actual property listings specifically on realtor.com.
    
    Args:
        location: The area to search (e.g., 'Palo Alto, CA').
        query: Optional keywords (e.g., '3 bedroom', 'under 2M').
        
    Returns:
        A list of results containing name, address, price, imageUrl, and realtorUrl.
    """
    # This tool is a signal to the agent to use Google Search grounding specifically for Realtor.com.
    # The agent should search for 'site:realtor.com [query] in [location]' and extract images/links.
    return []
