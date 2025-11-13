"""Page management operations."""
from typing import Optional
from playwright.async_api import Page
from .browser_manager import BrowserManager
from .interaction_manager import InteractionManager
from .websocket_message_sender import WebSocketMessageSender


class PageManager:
    """Manages page operations: switching, creating, and closing tabs."""
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        interaction_manager: InteractionManager,
        message_sender: WebSocketMessageSender
    ):
        """
        Initialize page manager.
        
        Args:
            browser_manager: BrowserManager instance
            interaction_manager: InteractionManager instance
            message_sender: WebSocketMessageSender instance
        """
        self.browser_manager = browser_manager
        self.interaction_manager = interaction_manager
        self.message_sender = message_sender
    
    async def switch_active_page(self, page_id: str) -> None:
        """
        Switch the active page for streaming and input handling.
        Single Responsibility: This method coordinates updating all page-dependent components.
        
        Args:
            page_id: UUID string of the page to switch to
        """
        if not self.browser_manager:
            await self.message_sender.send_error('Browser not initialized')
            return
        
        # Get the page instance
        page = self.browser_manager.get_page_by_id(page_id)
        if not page:
            await self.message_sender.send_error(f'Page with ID {page_id} not found')
            return
        
        try:
            # Bring the page to front and make it active
            await page.bring_to_front()
            
            # Update all page-dependent components atomically via interaction manager
            self.interaction_manager.set_page(page)
            
            # Update the main page reference
            self.browser_manager.page = page
            
            # Send confirmation to frontend with current URL
            current_url = page.url
            await self.message_sender.send_page_switched(page_id, current_url)
            
            print(f"[+] Switched to page: {page_id}")
        except Exception as e:
            print(f"Error switching page: {e}")
            await self.message_sender.send_error(f'Error switching page: {str(e)}')
    
    async def create_new_tab(self) -> None:
        """
        Create a new tab/page and navigate it to duckduckgo.com.
        The page will be automatically tracked and switched to via page_added_callback.
        """
        if not self.browser_manager or not self.browser_manager.context:
            await self.message_sender.send_error('Browser not initialized')
            return
        
        try:
            # Create a new page in the existing context
            # This will trigger the page_added_callback which will auto-switch to it
            new_page = await self.browser_manager.context.new_page()
            
            # Navigate to duckduckgo.com
            await new_page.goto('https://duckduckgo.com/', wait_until='commit')
            
            print(f"[+] Created new tab and navigated to duckduckgo.com")
        except Exception as e:
            print(f"Error creating new tab: {e}")
            await self.message_sender.send_error(f'Error creating new tab: {str(e)}')
    
    async def close_tab(self, page_id: str) -> None:
        """
        Close a tab/page by its ID.
        If closing the active page, switch to another available page.
        
        Args:
            page_id: UUID string of the page to close
        """
        if not self.browser_manager:
            await self.message_sender.send_error('Browser not initialized')
            return
        
        # Get the page instance
        page = self.browser_manager.get_page_by_id(page_id)
        if not page:
            await self.message_sender.send_error(f'Page with ID {page_id} not found')
            return
        
        # Check if this is the active page
        is_active_page = (self.browser_manager.page == page)
        
        try:
            # If closing the active page, switch to another page first to avoid errors
            if is_active_page:
                # Get all remaining pages (excluding the one we're about to close)
                all_page_ids = self.browser_manager.get_all_page_ids()
                remaining_page_ids = [pid for pid in all_page_ids if pid != page_id]
                
                if remaining_page_ids:
                    # Switch to the last remaining page before closing
                    await self.switch_active_page(remaining_page_ids[-1])
                else:
                    # No pages left, clear all page references before closing
                    self.browser_manager.page = None
                    self.interaction_manager.set_page(None)
            
            # Now close the page - this will trigger page_removed_callback to remove from dict
            await page.close()
            
            print(f"[+] Closed tab: {page_id}")
        except Exception as e:
            print(f"Error closing tab: {e}")
            await self.message_sender.send_error(f'Error closing tab: {str(e)}')

