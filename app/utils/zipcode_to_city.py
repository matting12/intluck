import httpx

async def zipcode_to_city(zipcode: str) -> str:
    """
    Convert US zipcode to 'City, State' format.
    Falls back to returning zipcode if lookup fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.zippopotam.us/us/{zipcode}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                place = data['places'][0]
                city = place['place name']
                state = place['state abbreviation']
                return f"{city}, {state}"
            else:
                logger.warning(f"Zipcode lookup failed for {zipcode}")
                return zipcode
                
    except Exception as e:
        logger.error(f"Zipcode conversion error: {e}")
        return zipcode  # Fallback to original input
    
