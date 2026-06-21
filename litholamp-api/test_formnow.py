import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to https://now.formlabs.com/")
        await page.goto("https://now.formlabs.com/")
        await page.wait_for_load_state("networkidle")
        print("Taking screenshot...")
        await page.screenshot(path="formnow_test.png", full_page=True)
        html = await page.content()
        with open("formnow_test.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Done!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
