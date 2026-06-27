import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating to TAB AFL page...")
        await page.goto("https://www.tab.com.au/sports/betting/AFL%20Football", timeout=60000)
        
        # Wait for content to load
        print("Waiting for page content to load...")
        await page.wait_for_timeout(5000) # give it 5 seconds
        
        # Get all text content on the page to analyze structure
        text = await page.evaluate("() => document.body.innerText")
        print("\n--- PAGE INNER TEXT ---")
        lines = text.split("\n")
        # print first 100 lines
        for line in lines[:150]:
            if line.strip():
                print(line)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
