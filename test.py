import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        async def on_new_page(new_page):
            print("New page opened:", new_page.url)
            await new_page.wait_for_load_state()
            print("New page loaded:", new_page.url)

        context.on("page", lambda new_page: asyncio.create_task(on_new_page(new_page)))

        await page.goto("https://example.com")

        # Wait indefinitely until browser is closed
        browser_closed = asyncio.Event()
        browser.once("disconnected", lambda: browser_closed.set())

        print("Waiting for browser to close manually...")
        await browser_closed.wait()

asyncio.run(main())
