"""Browser navigation operations."""
from .browser_manager import BrowserManager
from .websocket_message_sender import WebSocketMessageSender


class NavigationManager:
    """Handles browser navigation commands."""
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        message_sender: WebSocketMessageSender
    ):
        """
        Initialize navigation manager.
        
        Args:
            browser_manager: BrowserManager instance
            message_sender: WebSocketMessageSender instance
        """
        self.browser_manager = browser_manager
        self.message_sender = message_sender
    
    async def handle_navigation(self, data: dict) -> None:
        """
        Handle navigation commands (back, forward, refresh, goto).
        
        Args:
            data: Navigation command data with 'action' and optional 'url'
        """
        if not self.browser_manager or not self.browser_manager.page:
            await self.message_sender.send_error('Browser not initialized or no active page')
            return
        
        page = self.browser_manager.page
        action = data.get('action')
        
        try:
            if action == 'back':
                await page.go_back()
            elif action == 'forward':
                await page.go_forward()
            elif action == 'refresh':
                await page.reload()
            elif action == 'goto':
                url = data.get('url')
                if not url:
                    await self.message_sender.send_error('URL required for goto action')
                    return
                await page.goto(url, wait_until='commit')
            else:
                await self.message_sender.send_error(f'Unknown navigation action: {action}')
                return
            
            # Update address bar with current URL
            current_url = page.url
            await self.message_sender.send_url_changed(current_url)
            
            print(f"[+] Navigation: {action}")
        except Exception as e:
            print(f"Error in navigation: {e}")
            await self.message_sender.send_error(f'Navigation error: {str(e)}')

