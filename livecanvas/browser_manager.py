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
    
    def _map_key(self, key: str, code: str = None) -> str:
        """
        Map JavaScript key name/code to Playwright key name.
        
        Args:
            key: JavaScript key value (e.g., 'a', 'Enter', 'Control')
            code: JavaScript key code (e.g., 'KeyA', 'Enter', 'ControlLeft')
            
        Returns:
            Playwright key name
        """
        # Direct mapping for most keys
        key_map = {
            # Special keys
            'Enter': 'Enter',
            'Escape': 'Escape',
            'Tab': 'Tab',
            'Backspace': 'Backspace',
            'Delete': 'Delete',
            'Insert': 'Insert',
            'Home': 'Home',
            'End': 'End',
            'PageUp': 'PageUp',
            'PageDown': 'PageDown',
            'PrintScreen': 'PrintScreen',
            'Pause': 'Pause',
            'ScrollLock': 'ScrollLock',
            'NumLock': 'NumLock',
            'CapsLock': 'CapsLock',
            
            # Arrow keys
            'ArrowUp': 'ArrowUp',
            'ArrowDown': 'ArrowDown',
            'ArrowLeft': 'ArrowLeft',
            'ArrowRight': 'ArrowRight',
            
            # Function keys
            'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4',
            'F5': 'F5', 'F6': 'F6', 'F7': 'F7', 'F8': 'F8',
            'F9': 'F9', 'F10': 'F10', 'F11': 'F11', 'F12': 'F12',
            
            # Modifier keys
            'Control': 'Control',
            'Alt': 'Alt',
            'Shift': 'Shift',
            'Meta': 'Meta',
            
            # Whitespace
            ' ': 'Space',
            'Space': 'Space',
        }
        
        # Check direct mapping first
        if key in key_map:
            return key_map[key]
        
        # Handle single character keys (letters, numbers, symbols)
        if len(key) == 1:
            # Playwright expects lowercase for letters, but Shift is handled separately
            return key.lower() if key.isalpha() else key
        
        # Handle code-based mapping for special cases
        if code:
            code_map = {
                'Space': 'Space',
                'Enter': 'Enter',
                'Escape': 'Escape',
                'Tab': 'Tab',
                'Backspace': 'Backspace',
                'Delete': 'Delete',
                'Insert': 'Insert',
                'Home': 'Home',
                'End': 'End',
                'PageUp': 'PageUp',
                'PageDown': 'PageDown',
                'ArrowUp': 'ArrowUp',
                'ArrowDown': 'ArrowDown',
                'ArrowLeft': 'ArrowLeft',
                'ArrowRight': 'ArrowRight',
            }
            if code in code_map:
                return code_map[code]
        
        # Default: return key as-is (Playwright may accept it)
        return key
    
    async def key_down(self, key: str, code: str = None, modifiers: list = None) -> None:
        """
        Press a key in the browser.
        
        Args:
            key: JavaScript key value
            code: JavaScript key code (optional)
            modifiers: List of modifier keys ['Control', 'Alt', 'Shift', 'Meta']
            
        Raises:
            Exception: If key press fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        
        playwright_key = self._map_key(key, code)
        
        # Handle modifiers
        if modifiers:
            # Press modifiers first
            for mod in modifiers:
                if mod in ['Control', 'Alt', 'Shift', 'Meta']:
                    await self.page.keyboard.down(mod)
        
        # Press the main key
        await self.page.keyboard.down(playwright_key)
    
    async def key_up(self, key: str, code: str = None, modifiers: list = None) -> None:
        """
        Release a key in the browser.
        
        Args:
            key: JavaScript key value
            code: JavaScript key code (optional)
            modifiers: List of modifier keys ['Control', 'Alt', 'Shift', 'Meta']
            
        Raises:
            Exception: If key release fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        
        playwright_key = self._map_key(key, code)
        
        # Release the main key first
        await self.page.keyboard.up(playwright_key)
        
        # Release modifiers
        if modifiers:
            for mod in modifiers:
                if mod in ['Control', 'Alt', 'Shift', 'Meta']:
                    await self.page.keyboard.up(mod)
    
    async def type_text(self, text: str) -> None:
        """
        Type text in the browser.
        
        Args:
            text: Text to type
            
        Raises:
            Exception: If typing fails
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized")
        await self.page.keyboard.type(text)
    
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

