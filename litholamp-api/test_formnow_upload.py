import asyncio
import os
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to https://now.formlabs.com/")
        await page.goto("https://now.formlabs.com/")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        
        file_input = await page.query_selector('input[type="file"]')
        if not file_input:
            print("No file input found!")
            await browser.close()
            return
            
        print("Uploading blank STL...")
        stl_path = os.path.abspath("blank_stls/RoundWoodBase.stl")
        await file_input.set_input_files(stl_path)
        
        print("Waiting for navigation to /order/configure...")
        await page.wait_for_url("**/order/configure**", timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        print("Clicking 'Supports Attached'...")
        # There might be multiple elements with text "Supports Attached", so we wait for it to be visible
        supports_btn = page.locator('text="Supports Attached"').first
        await supports_btn.wait_for(state="visible")
        await supports_btn.click()
        
        print("Waiting for quoting to finish...")
        # When quoting is finished, there should be a price > $0.00 in the Total
        # Let's poll the page text for the Total price
        for i in range(20):
            await asyncio.sleep(1)
            # Find the element that contains "Total:" and the price next to it
            # The summary section usually has a distinctive block
            html = await page.content()
            # Try to regex the total price
            matches = re.findall(r'Total:\s*</div>.*?\$([0-9]+\.[0-9]{2})', html, re.IGNORECASE | re.DOTALL)
            if matches:
                price = float(matches[0])
                if price > 0.0:
                    print(f"SUCCESS! Found price: ${price}")
                    break
            else:
                # Fallback simple regex
                matches2 = re.findall(r'\$([0-9]{2,}\.[0-9]{2})', html)
                if matches2:
                    prices = [float(m) for m in matches2 if float(m) > 0.0]
                    if prices:
                        print(f"SUCCESS! Found raw prices: {prices}. Taking highest as total: ${max(prices)}")
                        break
        
        print("Taking final screenshot...")
        await page.screenshot(path="formnow_final.png", full_page=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
