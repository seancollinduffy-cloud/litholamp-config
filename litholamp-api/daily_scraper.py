import asyncio
import json
import os
import traceback
from playwright_formnow_buyer import get_formnow_quote

CONFIGS_TO_SCRAPE = [
    "RoundWoodBase",
    "DarkWoodBase",
    "TiffanyDesk",
    "TiffanyFloor",
    "SquareWoodBase_Portrait",
    "SquareWoodBase_Landscape"
]

async def run_daily_scraper():
    print("Starting daily scraper for FormNow pricing...")
    pricing = {}
    for hardware in CONFIGS_TO_SCRAPE:
        print(f"\n--- Scraping {hardware} ---")
        try:
            # We pass hardware name to get_formnow_quote which will look for blank_stls/{hardware}.stl
            # Height doesn't matter for the scraper as it reads the actual STL size, but we pass default 120
            price = await get_formnow_quote(hardware, 120.0)
            pricing[hardware] = price
            print(f"Success: {hardware} = ${price}")
        except Exception as e:
            print(f"Failed to scrape {hardware}: {e}")
            traceback.print_exc()

    # Save to JSON
    out_path = os.path.join(os.path.dirname(__file__), "todays_pricing.json")
    with open(out_path, "w") as f:
        json.dump(pricing, f, indent=4)
    print(f"\nSaved today's pricing to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_daily_scraper())
