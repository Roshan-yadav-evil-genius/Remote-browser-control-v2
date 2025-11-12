"""Browser management for Playwright browser instances."""
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional


class BrowserManager:
    """Manages Playwright browser lifecycle only."""
    
    def __init__(self, viewport_width: int = 640, viewport_height: int = 480):
        """
        Initialize browser manager.
        
        Args:
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def launch(self, url: str, headless: bool = False) -> Page:
        """
        Launch browser and navigate to URL.
        
        Args:
            url: URL to navigate to
            headless: Whether to run browser in headless mode
            
        Returns:
            Page instance
            
        Raises:
            Exception: If browser launch or navigation fails
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        # Create a new page with viewport matching canvas dimensions
        self.page = await self.browser.new_page(viewport={
            'width': self.viewport_width,
            'height': self.viewport_height
        })
        
        # Navigate to URL - don't wait for full page load, start streaming immediately
        # Using 'commit' means we return as soon as navigation is committed
        await self.page.goto(url, wait_until='commit')
        return self.page
    
    async def cleanup(self) -> None:
        """Clean up browser and Playwright instances."""
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                print(f"Error closing page: {e}")
            self.page = None
        
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                print(f"Error closing browser: {e}")
            self.browser = None
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                print(f"Error stopping playwright: {e}")
            self.playwright = None

