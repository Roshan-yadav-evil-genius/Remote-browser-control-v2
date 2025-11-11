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
    
    def _map_button(self, button: str) -> str:
        """
        Map button name to Playwright button name.
        
        Args:
            button: Button name ('left', 'right', 'middle')
            
        Returns:
            Playwright button name
        """
        button_map = {
            'left': 'left',
            'right': 'right',
            'middle': 'middle'
        }
        return button_map.get(button.lower(), 'left')
    
    async def move_mouse(self, x: int, y: int) -> None:
        """
        Move mouse to specified coordinates in the browser.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Raises:
            Exception: If move fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        await self.page.mouse.move(x, y)
    
    async def mouse_down(self, x: int, y: int, button: str = 'left') -> None:
        """
        Press mouse button at specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Button name ('left', 'right', 'middle')
            
        Raises:
            Exception: If mouse down fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        playwright_button = self._map_button(button)
        await self.page.mouse.move(x, y)
        await self.page.mouse.down(button=playwright_button)
    
    async def mouse_up(self, x: int, y: int, button: str = 'left') -> None:
        """
        Release mouse button at specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Button name ('left', 'right', 'middle')
            
        Raises:
            Exception: If mouse up fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        playwright_button = self._map_button(button)
        await self.page.mouse.move(x, y)
        await self.page.mouse.up(button=playwright_button)
    
    async def click(self, x: int, y: int, button: str = 'left') -> None:
        """
        Click at specified coordinates in the browser.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Button name ('left', 'right', 'middle')
            
        Raises:
            Exception: If click fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        playwright_button = self._map_button(button)
        await self.page.mouse.click(x, y, button=playwright_button)
    
    async def scroll(self, x: int, y: int, delta_x: float = 0, delta_y: float = 0) -> None:
        """
        Scroll at specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            delta_x: Horizontal scroll delta
            delta_y: Vertical scroll delta
            
        Raises:
            Exception: If scroll fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        await self.page.mouse.move(x, y)
        await self.page.mouse.wheel(delta_x, delta_y)
    
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

