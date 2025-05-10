import requests
import re
from collections import defaultdict

def parse_sites(sites, regions, country, make, budget):
    print(f"Parser called: sites={sites}, regions={regions}, country={country}, make={make}, budget={budget}")
    results = []
    
    if "bloket_swe" in sites and country == "sweden":
        region_map = {
            "stockholm": "Stockholm",
            "gothenburg": "Västra Götaland",
            "malmo": "Skåne"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
            "Accept": "application/json",
            "Authorization": "Bearer 7be0d6e292468a0ee93a6bc65a5518b22e8dd10f"
        }
        
        all_listings = []
        search_regions = regions if regions else list(region_map.keys())
        
        for region in search_regions:
            region_name = region_map.get(region.lower(), "Stockholm")
            url = "https://api.blocket.se/motor-search-service/v4/search/car"
            params = {
                "q": make if make else "",
                "filter": f'{{"key":"region","values":["{region_name}"]}}',
                "page": "1"
            }
            
            print(f"API request: {url}, params={params}")
            try:
                response = requests.get(url, params=params, headers=headers, timeout=5)
                print(f"Status: {response.status_code}")
                print(f"Server response: {response.text[:500]}")
                data = response.json()
                listings = data.get("cars", []) if data.get("cars") is not None else []
                
                for listing in listings:
                    title = listing.get("heading", "No title").lower()
                    price_data = listing.get("price", {})
                    price_str = price_data.get("amount", "No price")
                    link = listing.get("link", "No link")
                    description = listing.get("description", "").lower()
                    seller_type = listing.get("seller", {}).get("type", "Unknown").lower()
                    
                    if price_str != "No price":
                        price = int(price_str.replace(" kr", "").replace(" ", ""))
                        is_leasing = False
                        
                        leasing_keywords = ["leasing", "månad", "per month", "month", "hyra", "kr/mån"]
                        has_leasing_keywords = any(keyword in title for keyword in leasing_keywords) or \
                                               any(keyword in description for keyword in leasing_keywords)
                        if has_leasing_keywords:
                            is_leasing = True
                        
                        if not is_leasing and price <= budget:
                            if not make or make.lower() in title:
                                year_match = re.search(r'\b(19|20)\d{2}\b', title)
                                year = int(year_match.group(0)) if year_match else None
                                model = title.split(str(year))[0].strip() if year else title.split(",")[0].strip()
                                
                                all_listings.append({
                                    "title": title,
                                    "price": price,
                                    "link": link,
                                    "region": region_name,
                                    "year": year,
                                    "model": model
                                })
            except Exception as e:
                print(f"HTTP error: {e}")
                results.append(f"Error for {region}: {e}")
        
        if all_listings:
            model_groups = defaultdict(list)
            no_year_listings = []
            for listing in all_listings:
                if listing["year"]:
                    model_groups[listing["model"]].append(listing)
                else:
                    no_year_listings.append(listing)
            
            filtered_listings = []
            for model, listings in model_groups.items():
                for listing in listings:
                    year = listing["year"]
                    similar = [l for l in listings if abs(l["year"] - year) <= 3]
                    if similar:
                        cheapest = min(similar, key=lambda x: x["price"])
                        if cheapest not in filtered_listings:
                            filtered_listings.append(cheapest)
            
            filtered_listings.extend(no_year_listings)
            cheap_listings = sorted(filtered_listings, key=lambda x: x["price"])[:3]
            for listing in cheap_listings:
                results.append(f"[{listing['title']}]({listing['link']}) - {listing['price']} kr - {listing['region']}")
        else:
            results.append("No listings with full price found within your budget")
    
    print(f"Parser result: {results}")
    return results if results else ["Nothing found"]