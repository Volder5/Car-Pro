from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

site_options = {
    "sweden": {
        "sites": [
            ("Blocket", "site_bloket_swe"),
            ("Bytbil", "site_bytbil_swe"),
            ("Bilweb", "site_bilweb_swe")
        ],
        "regions": [
            ("Stockholm", "region_stockholm"),
            ("Gothenburg", "region_gothenburg"),
            ("Malmo", "region_malmo")
        ]
    },
    "norway": {
        "sites": [
            ("Blocket", "site_bloket_nor"),
            ("Finn.no", "site_finn_nor")
        ],
        "regions": [
            ("Oslo", "region_oslo"),
            ("Bergen", "region_bergen")
        ]
    },
    "finland": {
        "sites": [
            ("Tori.fi", "site_tori_fin")
        ],
        "regions": [
            ("Helsinki", "region_helsinki"),
            ("Tampere", "region_tampere")
        ]
    }
}

menus = {
    "main": {
        "text": "Main menu",
        "keyboard": (InlineKeyboardBuilder()
                     .add(InlineKeyboardButton(text="Search parameters", callback_data="params"))
                     .add(InlineKeyboardButton(text="Pricing", callback_data="tariffs"))
                     .adjust(2)
                     .as_markup())
    },
    "params": {
        "text": "Search parameters",
        "keyboard": (InlineKeyboardBuilder()
                     .add(InlineKeyboardButton(text="Countries", callback_data="countryChoose"))
                     .add(InlineKeyboardButton(text="Regions", callback_data="regions"))
                     .add(InlineKeyboardButton(text="Choose make", callback_data="choose_make"))
                     .add(InlineKeyboardButton(text="Set budget", callback_data="set_budget"))
                     .add(InlineKeyboardButton(text="Back", callback_data="main"))
                     .adjust(2)
                     .as_markup())
    },
    "countryChoose": {
        "text": "Choose a country",
        "keyboard": (InlineKeyboardBuilder()
                     .add(*[InlineKeyboardButton(text=country.capitalize(), callback_data=country)
                            for country in site_options.keys()])
                     .add(InlineKeyboardButton(text="Back", callback_data="params"))
                     .adjust(2)
                     .as_markup())
    },
    "regions": {
        "text": "Choose regions",
        "keyboard": (InlineKeyboardBuilder()
                     .add(InlineKeyboardButton(text="Sweden", callback_data="region_sweden"))
                     .add(InlineKeyboardButton(text="Norway", callback_data="region_norway"))
                     .add(InlineKeyboardButton(text="Finland", callback_data="region_finland"))
                     .add(InlineKeyboardButton(text="Back", callback_data="params"))
                     .adjust(2)
                     .as_markup())
    },
    "tariffs": {
        "text": "Pricing (placeholder)",
        "keyboard": (InlineKeyboardBuilder()
                     .add(InlineKeyboardButton(text="Back", callback_data="main"))
                     .adjust(2)
                     .as_markup())
    }
}

for country in ["sweden", "norway", "finland"]:
    menus[f"region_{country}"] = {
        "text": f"Regions for {country.capitalize()}",
        "keyboard": (InlineKeyboardBuilder()
                     .add(*[InlineKeyboardButton(text=name, callback_data=data)
                            for name, data in site_options[country]["regions"]])
                     .add(InlineKeyboardButton(text="Back", callback_data="regions"))
                     .adjust(1)
                     .as_markup())
    }