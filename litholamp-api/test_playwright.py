import asyncio
from playwright.async_api import async_playwright

async def test_xometry():
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
        
        print("Waiting for login to complete...")
        await asyncio.sleep(5)
        
        print("Navigating to Quoting...")
        await page.goto("https://get.xometry.com/quote")
        await asyncio.sleep(5)
        
        print("URL after quote nav:", page.url)
        await page.screenshot(path="xometry_quote.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_xometry())
