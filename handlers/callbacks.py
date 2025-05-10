from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import keyboards as kb
from database import Database
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

router = Router()
listings_storage = {}

class MakeSelection(StatesGroup):
    waiting_for_make = State()

SITE_NAMES = {
    "bloket_swe": "Blocket",
    "bytbil_swe": "Bytbil",
    "bilweb_swe": "Bilweb",
    "bloket_nor": "Blocket",
    "finn_nor": "Finn.no",
    "tori_fin": "Tori.fi",
}

@router.callback_query(lambda c: c.data == "main")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(kb.menus["main"]["text"], reply_markup=kb.menus["main"]["keyboard"])
    await callback.answer()

@router.callback_query(lambda c: c.data == "params")
async def handle_params(callback: CallbackQuery):
    await callback.message.edit_text(kb.menus["params"]["text"], reply_markup=kb.menus["params"]["keyboard"])
    await callback.answer()

@router.callback_query(lambda c: c.data == "tariffs")
async def handle_tariffs(callback: CallbackQuery):
    await callback.message.edit_text(kb.menus["tariffs"]["text"], reply_markup=kb.menus["tariffs"]["keyboard"])
    await callback.answer()

@router.callback_query(lambda c: c.data == "countryChoose")
async def handle_country_choose(callback: CallbackQuery):
    await callback.message.edit_text(kb.menus["countryChoose"]["text"], reply_markup=kb.menus["countryChoose"]["keyboard"])
    await callback.answer()

@router.callback_query(lambda c: c.data == "regions")
async def handle_regions(callback: CallbackQuery):
    await callback.message.edit_text(kb.menus["regions"]["text"], reply_markup=kb.menus["regions"]["keyboard"])
    await callback.answer()

@router.callback_query(lambda c: c.data in kb.site_options.keys())
async def handle_country_selection(callback: CallbackQuery, db: Database):
    country = callback.data
    user_id = callback.from_user.id
    current_sites = db.get_user_sites(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if site.replace('site_', '') in current_sites else ''}",
            callback_data=f"{site}"
        )] for name, site in kb.site_options[country]["sites"]
    ] + [[InlineKeyboardButton(text="Back", callback_data="countryChoose")]])
    
    await callback.message.edit_text(f"Select sites for {country.capitalize()}:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("site_"))
async def handle_site_selection(callback: CallbackQuery, db: Database):
    site_data = callback.data
    logging.debug(f"Selected site: {site_data}")
    
    site = site_data.replace("site_", "")
    user_id = callback.from_user.id
    
    country = None
    for c, opts in kb.site_options.items():
        if any(data.replace("site_", "") == site for _, data in opts["sites"]):
            country = c
            break
    
    if not country:
        logging.error(f"Country for site {site} not found in site_options: {kb.site_options}")
        await callback.message.edit_text("Error: site not found.", reply_markup=kb.menus["params"]["keyboard"])
        await callback.answer()
        return
    
    db.toggle_site(user_id, site)
    current_sites = db.get_user_sites(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if s.replace('site_', '') in current_sites else ''}",
            callback_data=f"{s}"
        )] for name, s in kb.site_options[country]["sites"]
    ] + [[InlineKeyboardButton(text="Back", callback_data="countryChoose")]])
    
    await callback.message.edit_text(f"Select sites for {country.capitalize()}:", reply_markup=keyboard)
    logging.debug(f"Site {site} processed for user_id={user_id}, current sites: {current_sites}")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("region_") and c.data not in [f"region_{country}" for country in kb.site_options.keys()])
async def handle_region_selection(callback: CallbackQuery, db: Database):
    region_data = callback.data  # For example, "region_stockholm"
    logging.debug(f"Selected region: {region_data}")
    
    country = None
    for c, opts in kb.site_options.items():
        if any(data == region_data for _, data in opts["regions"]):
            country = c
            break
    
    if not country:
        logging.error(f"Country for region {region_data} not found in site_options: {kb.site_options}")
        await callback.message.edit_text("Error: region not found.", reply_markup=kb.menus["regions"]["keyboard"])
        await callback.answer()
        return
    
    db.toggle_region(callback.from_user.id, region_data.replace("region_", ""))
    current_regions = db.get_user_regions(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if r.replace('region_', '') in current_regions else ''}",
            callback_data=f"{r}"
        )] for name, r in kb.site_options[country]["regions"]
    ] + [[InlineKeyboardButton(text="Back", callback_data="regions")]])
    
    await callback.message.edit_text(f"Select regions for {country.capitalize()}:", reply_markup=keyboard)
    logging.debug(f"Region {region_data} processed for user_id={callback.from_user.id}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "choose_make")
async def handle_choose_make(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    current_makes = db.get_user_makes(user_id)
    
    popular_makes = [
        ("BMW", "bmw"), ("Volvo", "volvo"),
        ("Mercedes", "mercedes"), ("Volkswagen", "volkswagen"),
        ("Audi", "audi"), ("Toyota", "toyota"),
        ("Ford", "ford"), ("Honda", "honda")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if make in current_makes else ''}",
            callback_data=f"make_{make}"
        ) for name, make in popular_makes[i:i+2]] for i in range(0, len(popular_makes), 2)
    ] + [
        [InlineKeyboardButton(text="Select manually", callback_data="make_manual"),
         InlineKeyboardButton(text="Back", callback_data="params")]
    ])
    
    await callback.message.edit_text("Select brands:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("make_") and c.data != "make_manual")
async def handle_make_selection(callback: CallbackQuery, db: Database):
    make_data = callback.data.replace("make_", "")  # For example, "bmw"
    logging.debug(f"Selected brand: {make_data}")
    user_id = callback.from_user.id
    
    db.toggle_make(user_id, make_data)
    current_makes = db.get_user_makes(user_id)
    
    popular_makes = [
        ("BMW", "bmw"), ("Volvo", "volvo"),
        ("Mercedes", "mercedes"), ("Volkswagen", "volkswagen"),
        ("Audi", "audi"), ("Toyota", "toyota"),
        ("Ford", "ford"), ("Honda", "honda")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if make in current_makes else ''}",
            callback_data=f"make_{make}"
        ) for name, make in popular_makes[i:i+2]] for i in range(0, len(popular_makes), 2)
    ] + [
        [InlineKeyboardButton(text="Select manually", callback_data="make_manual"),
         InlineKeyboardButton(text="Back", callback_data="params")]
    ])
    
    await callback.message.edit_text("Select brands:", reply_markup=keyboard)
    logging.debug(f"Brand {make_data} processed for user_id={user_id}, current brands: {current_makes}")
    await callback.answer()

@router.callback_query(lambda c: c.data == "make_manual")
async def handle_make_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter the brand manually:", reply_markup=None)
    await state.set_state(MakeSelection.waiting_for_make)
    await callback.answer()

@router.message(MakeSelection.waiting_for_make)
async def process_make_input(message: CallbackQuery, state: FSMContext, db: Database):
    make = message.text.strip().lower()  # Convert input to lowercase
    user_id = message.from_user.id
    
    db.toggle_make(user_id, make)
    current_makes = db.get_user_makes(user_id)
    
    popular_makes = [
        ("BMW", "bmw"), ("Volvo", "volvo"),
        ("Mercedes", "mercedes"), ("Volkswagen", "volkswagen"),
        ("Audi", "audi"), ("Toyota", "toyota"),
        ("Ford", "ford"), ("Honda", "honda")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if make in current_makes else ''}",
            callback_data=f"make_{make}"
        ) for name, make in popular_makes[i:i+2]] for i in range(0, len(popular_makes), 2)
    ] + [
        [InlineKeyboardButton(text="Select manually", callback_data="make_manual"),
         InlineKeyboardButton(text="Back", callback_data="params")]
    ])
    
    await message.reply("Select brands:", reply_markup=keyboard)
    await state.clear()

@router.callback_query(lambda c: c.data == "none")
async def sites_choose(callback: CallbackQuery):
    await callback.answer("Developing nigga!", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("view_listings_"))
async def handle_view_listings(callback: CallbackQuery, db: Database):
    global listings_storage
    user_id = callback.from_user.id
    data_parts = callback.data.split("_")
    
    if len(data_parts) < 3 or data_parts[0] != "view" or data_parts[1] != "listings":
        logging.error(f"Invalid callback_data format: {callback.data}, data_parts={data_parts}")
        await callback.message.edit_text("Error processing request", reply_markup=None)
        await callback.answer()
        return

    try:
        target_user_id = int(data_parts[2])
        page = int(data_parts[3]) if len(data_parts) > 3 else 0
    except ValueError as e:
        logging.error(f"Conversion error in callback_data '{callback.data}': {e}")
        await callback.message.edit_text("Error processing request", reply_markup=None)
        await callback.answer()
        return

    if user_id != target_user_id:
        await callback.answer("These are not your listings!", show_alert=True)
        return

    if user_id not in listings_storage or not listings_storage[user_id]:
        await callback.message.edit_text("No listings to display")
        await callback.answer()
        return

    sites = {}
    for listing in listings_storage[user_id]:
        site = listing.get("site")
        if site:
            sites[site] = sites.get(site, 0) + 1

    if not sites:
        await callback.message.edit_text("No sites with listings")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{SITE_NAMES.get(site, site)} ({count})", callback_data=f"view_site_{user_id}_{site}_0")]
        for site, count in sites.items()
    ])

    await callback.message.edit_text("Select a site to view:", reply_markup=keyboard)
    logging.debug(f"Displayed site menu for user_id={user_id}: {sites}")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("view_site_"))
async def handle_site_selection_listings(callback: CallbackQuery, db: Database):
    global listings_storage
    user_id = callback.from_user.id

    data_parts = callback.data.split("_")
    logging.debug(f"Raw callback.data: '{callback.data}', split result: {data_parts}")

    if len(data_parts) < 5 or data_parts[0] != "view" or data_parts[1] != "site":
        logging.error(f"Invalid callback_data format: {callback.data}, data_parts={data_parts}")
        await callback.message.edit_text("Error processing request", reply_markup=None)
        await callback.answer()
        return

    try:
        target_user_id = int(data_parts[2])
        index = int(data_parts[-1])
        site = "_".join(data_parts[3:-1])
        logging.debug(f"Parsed: user_id={user_id}, target_user_id={target_user_id}, site={site}, index={index}")
    except (ValueError, IndexError) as e:
        logging.error(f"Conversion error in callback_data '{callback.data}': {e}")
        await callback.message.edit_text("Error processing request", reply_markup=None)
        await callback.answer()
        return

    if str(user_id) != str(target_user_id):
        logging.debug(f"Access denied: user_id={user_id} != target_user_id={target_user_id}")
        await callback.answer("These are not your listings!", show_alert=True)
        return

    if user_id not in listings_storage or not listings_storage[user_id]:
        logging.debug(f"No listings for user_id={user_id}")
        await callback.message.edit_text("No listings to display")
        await callback.answer()
        return

    listings = [l for l in listings_storage[user_id] if l.get("site") == site]
    logging.debug(f"Found {len(listings)} listings for site {site} for user_id={user_id}")

    if not listings:
        logging.debug(f"No listings for site {site} for user_id={user_id}")
        await callback.message.edit_text(f"No listings from site {site}")
        await callback.answer()
        return

    index = max(0, min(index, len(listings) - 1))
    logging.debug(f"Listings length={len(listings)}, adjusted index={index}")

    try:
        listing = listings[index]
        if not isinstance(listing, dict) or "message" not in listing:
            logging.error(f"Invalid listing format: {listing}")
            await callback.message.edit_text("Error in listing data", reply_markup=None)
            await callback.answer()
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Back", callback_data=f"view_site_{user_id}_{site}_{index-1}" if index > 0 else "noop"),
                InlineKeyboardButton(text=f"{index+1}/{len(listings)}", callback_data="noop"),
                InlineKeyboardButton(text="Next", callback_data=f"view_site_{user_id}_{site}_{index+1}" if index < len(listings)-1 else "noop")
            ],
            [InlineKeyboardButton(text="Return to sites", callback_data=f"view_listings_{user_id}_0")]
        ])

        await callback.message.edit_text(listing["message"], reply_markup=keyboard, parse_mode="Markdown")
        logging.debug(f"Displayed listing index={index} from site {site}: {listing['message'][:50]}...")

    except Exception as e:
        logging.error(f"Error in handle_site_selection_listings: {e}", exc_info=True)
        await callback.message.edit_text("Trouble processing command", reply_markup=None)

    await callback.answer()

@router.callback_query(lambda c: c.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(lambda c: c.data in [f"region_{country}" for country in kb.site_options.keys()])
async def handle_region_country(callback: CallbackQuery, db: Database):
    country = callback.data.replace("region_", "")  # For example, "sweden"
    user_id = callback.from_user.id
    current_regions = db.get_user_regions(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{name} {'✅' if region.replace('region_', '') in current_regions else ''}",
            callback_data=f"{region}"
        )] for name, region in kb.site_options[country]["regions"]
    ] + [[InlineKeyboardButton(text="Back", callback_data="regions")]])
    
    await callback.message.edit_text(f"Select regions for {country.capitalize()}:", reply_markup=keyboard)
    await callback.answer()