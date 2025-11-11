"""Browser management for Playwright browser instances."""
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional


class BrowserManager:
    """Manages Playwright browser lifecycle and page operations."""
    
    def __init__(self, viewport_width: int = 640, viewport_height: int = 480):
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
        
        # Navigate to URL
        await self.page.goto(url)
        
        # Wait for page to load
        await self.page.wait_for_load_state('networkidle')
        
        return self.page
    
    async def click(self, x: int, y: int) -> None:
        """
        Click at specified coordinates in the browser.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Raises:
            Exception: If click fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        await self.page.mouse.click(x, y)
    
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

