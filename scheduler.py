from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import re
from collections import defaultdict
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.callbacks import listings_storage 

listings_buffer = []

def setup_scheduler(bot, db):
    scheduler = AsyncIOScheduler()

    async def update_model_average_price(model):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
            "Accept": "application/json",
            "Authorization": "Bearer 7be0d6e292468a0ee93a6bc65a5518b22e8dd10f"
        }
        url = "https://api.blocket.se/motor-search-service/v4/search/car"
        prices_by_year = defaultdict(list)
        page = 1
        current_year = datetime.now().year
        
        while True:
            params = {"q": model, "page": str(page)}
            print(f"Gathering data for {model}, page {page}: {url}, params={params}")
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
                print(f"Status: {response.status_code}")
                data = response.json()
                listings = data.get("cars", []) if data.get("cars") is not None else []
                
                if not listings:
                    print(f"Page {page} is empty for {model}, stopping")
                    break
                
                for listing in listings:
                    title = listing.get("heading", "No title").lower()
                    price_data = listing.get("price", {})
                    price_str = price_data.get("amount", "No price")
                    billing_period = price_data.get("billingPeriod", "single")
                    car_data = listing.get("car", {})
                    reg_date = car_data.get("regDate", None)
                    
                    is_leasing = (billing_period != "single" or 
                                 any(keyword in title for keyword in ["leasing", "månad", "per month", 
                                                                      "month", "hyra", "kr/mån", "företagsleasing"]))
                    if price_str == "No price" or is_leasing:
                        continue
                    
                    price = int(price_str.replace(" kr", "").replace(" ", ""))
                    year_match = re.search(r'(19|20)\d{2}', title)
                    year = int(year_match.group(0)) if year_match else (int(str(reg_date)[:4]) if reg_date else None)
                    if not year or year < 1950 or year > current_year + 1:
                        year = int(str(reg_date)[:4]) if reg_date else None
                    if not year or year < 1950 or year > current_year + 1:
                        continue
                    
                    prices_by_year[year].append(price)
                
                page += 1
            
            except Exception as e:
                print(f"Error gathering data for {model} on page {page}: {e}")
                break

        for year in prices_by_year.keys():
            year_range = range(max(1950, year - 3), min(current_year + 1, year + 4))
            range_prices = [p for y, ps in prices_by_year.items() if y in year_range for p in ps]
            if range_prices:
                avg_price = sum(range_prices) // len(range_prices)
                min_price, max_price = min(range_prices), max(range_prices)
                db.update_average_price(model, year, avg_price)
                print(f"Updated average price for {model} ({year - 3}–{year + 3}): {avg_price:,} kr "
                      f"(based on {len(range_prices)} listings, min: {min_price:,} kr, max: {max_price:,} kr)")

    async def check_new_listings():
        global listings_buffer
        
        users = db.get_all_users()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
            "Accept": "application/json",
            "Authorization": "Bearer 7be0d6e292468a0ee93a6bc65a5518b22e8dd10f"
        }
        region_map = {"stockholm": "Stockholm", "gothenburg": "Västra Götaland", "malmo": "Skåne"}
        
        for user_id, sites, regions, make, budget in users:
            if not sites or not budget:
                print(f"User {user_id}: no sites or budget, skipping")
                continue
            
            sites_list = sites.split(",")
            regions_list = regions.split(",") if regions else list(region_map.keys())
            print(f"User {user_id}: sites={sites_list}, regions={regions_list}, make={make}, budget={budget}")
            
            if "bloket_swe" not in sites_list:
                print(f"User {user_id}: Blocket not selected, skipping")
                continue
            
            for region in regions_list:
                region_name = region_map.get(region.lower(), "Stockholm")
                url = "https://api.blocket.se/motor-search-service/v4/search/car"
                params = {
                    "q": make if make else "",
                    "filter": f'{{"key":"region","values":["{region_name}"]}}',
                    "page": "1"
                }
                
                print(f"API request for {region_name}: {url}, params={params}")
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=5, verify=False)
                    print(f"Status: {response.status_code}")
                    data = response.json()
                    listings = data.get("cars", []) if data.get("cars") is not None else []
                    print(f"Listings found: {len(listings)}")
                    
                    for listing in listings:
                        title = listing.get("heading", "No title").lower()
                        price_data = listing.get("price", {})
                        price_str = price_data.get("amount", "No price")
                        billing_period = price_data.get("billingPeriod", "single")
                        link = listing.get("link", "No link")
                        car_data = listing.get("car", {})
                        reg_date = car_data.get("regDate", None)
                        
                        if price_str == "No price":
                            continue
                        
                        price = int(price_str.replace(" kr", "").replace(" ", ""))
                        is_leasing = (billing_period != "single" or 
                                    any(keyword in title for keyword in ["leasing", "månad", "per month", 
                                                                        "month", "hyra", "kr/mån", "företagsleasing"]))
                        if is_leasing or price > budget:
                            print(f"Filtered out: {title} (leasing={is_leasing}, price={price} > budget={budget})")
                            continue
                        
                        if make and make.lower() not in title:
                            print(f"Filtered out: {title} (make {make} not found)")
                            continue
                        
                        year_match = re.search(r'(19|20)\d{2}', title)
                        current_year = datetime.now().year
                        year = int(year_match.group(0)) if year_match else (int(str(reg_date)[:4]) if reg_date else None)
                        if not year or year < 1950 or year > current_year + 1:
                            year = int(str(reg_date)[:4]) if reg_date else None
                        if not year or year < 1950 or year > current_year + 1:
                            continue
                        
                        if db.is_listing_sent(link):
                            print(f"Filtered out: {title} (already sent)")
                            continue
                        
                        model_parts = title.split()
                        model = " ".join(model_parts[:2]).replace("wolksvagen", "volkswagen")
                        avg_price, updated_at = db.get_average_price(model, year)
                        if avg_price and updated_at:
                            updated_at_dt = datetime.fromisoformat(updated_at)
                            if datetime.now() - updated_at_dt > timedelta(hours=48):
                                await update_model_average_price(model)
                                avg_price, _ = db.get_average_price(model, year)
                        elif not avg_price:
                            await update_model_average_price(model)
                            avg_price, _ = db.get_average_price(model, year)
                        
                        year_str = f" ({year})"
                        title_formatted = title.replace(year_str.strip(), "").strip()
                        message = (f"[{title_formatted}{year_str}]\n"
                                f"Price: {price:,} kr\n"
                                f"Link: {link}")
                        if avg_price:
                            discount_percent = (avg_price - price) / avg_price * 100
                            if discount_percent >= 20:
                                message += f"\nCheaper by {avg_price - price:,} kr ({discount_percent:.1f}% below average {avg_price:,} kr)"
                        
                        listings_buffer.append({
                            "user_id": user_id,
                            "message": message,
                            "site": "bloket_swe",
                            "link": link
                        })
                        print(f"Added: {title} (price={price}, link={link})")
                        db.add_sent_listing(link)
                    
                except Exception as e:
                    print(f"Scheduler error: {e}")

        if listings_buffer:
            user_counts = defaultdict(int)
            site_counts = defaultdict(int)
            for listing in listings_buffer:
                user_counts[listing["user_id"]] += 1
                site_counts[listing["site"]] += 1
            
            for user_id in user_counts:
                total = user_counts[user_id]
                listings_storage[user_id] = [l for l in listings_buffer if l["user_id"] == user_id]
                print(f"Saved for user_id {user_id}: {listings_storage[user_id]}")
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"Blocket ({site_counts['bloket_swe']})", callback_data=f"view_site_{user_id}_bloket_swe_0")]
                    if "bloket_swe" in site_counts else []
                ] + [[InlineKeyboardButton(text="Back", callback_data="main")]])
                message = f"Found {total} cars in the last hour\nChoose a site to view:"
                
                await bot.send_message(user_id, message, reply_markup=keyboard)
            
            listings_buffer.clear()

    scheduler.add_job(check_new_listings, "interval", minutes=1)
    return scheduler