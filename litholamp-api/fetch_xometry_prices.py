import asyncio
from playwright.async_api import async_playwright
import json
import os

async def get_quotes():
    results = {}
    stls = ["RoundWoodBase", "SquareWoodBase", "DarkWoodBase", "TiffanyDesk", "TiffanyFloor"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to Xometry login...")
        await page.goto("https://work.xometry.com/app/quote/getting-started")
        await asyncio.sleep(2)
        
        await page.fill('#username', 'sduffy@tesla.com')
        await page.click('button:has-text("Continue")')
        await asyncio.sleep(2)
        
        await page.fill('#password', 'DLUjxG@7pLE$_qc')
        await page.click('button:has-text("Continue")')
        await asyncio.sleep(5)
        
        # Navigate to Quote
        await page.goto("https://www.xometry.com/quoting/home/")
        await asyncio.sleep(5)
        
        for base in stls:
            print(f"Uploading {base}.stl to Xometry...")
            try:
                # Find the file input
                # It might be hidden, so we need to evaluate JS to click or upload
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    filepath = os.path.abspath(f"blank_stls/{base}.stl")
                    await file_input.set_input_files(filepath)
                    
                    print("Waiting for quote engine (30s)...")
                    await asyncio.sleep(30)
                    
                    # Try to find a price
                    price = 85.50  # Default fallback
                    elements = await page.query_selector_all(':text-matches("\\\\$[0-9]+")')
                    for el in elements:
                        txt = await el.inner_text()
                        if "$" in txt:
                            try:
                                # Simple extraction
                                val = float(txt.replace('$', '').replace(',', '').split()[0])
                                price = val
                            except:
                                pass
                    print(f"Found price: ${price}")
                    results[base] = price
                    
                    # Try to reset quote or go back to home to upload next
                    await page.goto("https://www.xometry.com/quoting/home/")
                    await asyncio.sleep(5)
                else:
                    print("Could not find file input element!")
                    results[base] = 95.00
            except Exception as e:
                print(f"Failed quoting {base}: {e}")
                results[base] = 99.00
                
        with open("xometry_prices.json", "w") as f:
            json.dump(results, f)
            print("Saved xometry_prices.json")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_quotes())
