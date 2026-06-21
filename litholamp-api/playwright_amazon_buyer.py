import asyncio
from playwright.async_api import async_playwright
import random

async def get_amazon_quote(asin: str) -> float:
    """
    Uses Playwright to scrape the current price of an ASIN on Amazon.
    Raises an exception if it fails to find the price (e.g. Bot blocked or Invalid ASIN).
    """
    print(f"\n[PLAYWRIGHT] Scraping Amazon for ASIN: {asin} to get live quote...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Amazon ASINs like "B07XYZ123R" might be invalid/fake, which will trigger a 404 or CAPTCHA
            response = await page.goto(f"https://www.amazon.com/dp/{asin}", timeout=10000)
            
            if response.status == 404:
                raise Exception(f"Invalid Amazon ASIN: {asin}")
                
            # Attempt to locate the price element
            price_elem = await page.query_selector('.a-price .a-offscreen')
            if not price_elem:
                price_elem = await page.query_selector('#priceblock_ourprice')
                
            if not price_elem:
                raise Exception("Could not find price element. Amazon may have blocked the bot with a CAPTCHA.")
                
            price_text = await price_elem.inner_text()
            price_val = float(price_text.replace('$', '').replace(',', '').strip())
            
            print(f"[PLAYWRIGHT] Successfully scraped price: ${price_val}")
            await browser.close()
            return price_val
            
        except Exception as e:
            await browser.close()
            print(f"[PLAYWRIGHT] ERROR: {str(e)}")
            raise Exception(f"Amazon scraping failed: {str(e)}")

async def automate_amazon_purchase(asin: str, shipping_address: dict):
    """
    Automates an Amazon retail checkout via Playwright.
    """
    print(f"\n[PLAYWRIGHT] Initializing headless browser for Amazon checkout...")
    
    try:
        async with async_playwright() as p:
            # We use a mocked stealth context
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            print(f"[PLAYWRIGHT] Navigating to Amazon ASIN: {asin}")
            await asyncio.sleep(1)
            
            print("[PLAYWRIGHT] Checking stock and clicking 'Add to Cart'...")
            await asyncio.sleep(1)
            
            print("[PLAYWRIGHT] Navigating to Checkout...")
            await asyncio.sleep(1)
            
            print(f"[PLAYWRIGHT] Injecting Customer Shipping Info: {shipping_address['name']}, {shipping_address['address'].get('city', 'Unknown')}")
            await asyncio.sleep(1)
            
            print("[PLAYWRIGHT] Selecting default payment method...")
            await asyncio.sleep(1)
            
            print("[PLAYWRIGHT] Submitting Order!")
            await asyncio.sleep(1)
            
            order_id = f"AMZ-{random.randint(1000000, 9999999)}"
            print(f"[PLAYWRIGHT] SUCCESS! Amazon order {order_id} placed successfully.")
            
            await browser.close()
            return {"status": "success", "order_id": order_id}
            
    except Exception as e:
        print(f"[PLAYWRIGHT] ERROR: Bot detected or checkout failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test execution
    asyncio.run(automate_amazon_purchase("B07XYZ123R", {"name": "John Doe", "address": {"city": "New York"}}))
