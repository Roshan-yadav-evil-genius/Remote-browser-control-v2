"""WebSocket consumer for video streaming."""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .browser_manager import BrowserManager
from .screenshot_streamer import ScreenshotStreamer
from .config import StreamConfig
from .message_router import MessageRouter
from .event_handlers.mouse_handler import MouseHandler
from .event_handlers.keyboard_handler import KeyboardHandler
from .controllers.mouse_controller import MouseController
from .controllers.keyboard_controller import KeyboardController
from .validators import MessageValidator


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that handles video streaming via browser screenshots."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        self.streaming = False
        self.browser_manager: BrowserManager = None
        self.streaming_task = None
        
        # Initialize controllers and streamer without pages (lazy initialization)
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        
        # Initialize message router with handlers
        self.message_router = MessageRouter(
            mouse_handler=MouseHandler(self.mouse_controller),
            keyboard_handler=KeyboardHandler(self.keyboard_controller),
            start_callback=None  # Already handled
        )
        
        # Initialize screenshot streamer without page
        self.screenshot_streamer = ScreenshotStreamer(
            fps=StreamConfig.STREAMING_FPS
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        self.streaming = False
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
        if self.screenshot_streamer:
            self.screenshot_streamer.stop()
        if self.browser_manager:
            await self.browser_manager.cleanup()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        print(f"Received message: {text_data}")
        try:
            validator = MessageValidator()
            data = validator.validate_json(text_data)
            message_type = validator.validate_message_type(data)
            
            # Handle 'start' message before router is initialized
            if message_type == 'start' and not self.streaming:
                self.streaming_task = asyncio.create_task(self.start_streaming())
            # Handle 'page_switch' message - needs access to browser_manager and controllers
            elif message_type == 'page_switch':
                if 'page_id' in data:
                    await self.switch_active_page(data['page_id'])
                else:
                    await self.send_error('page_switch message missing page_id')
            # Handle 'navigate' message - navigation commands
            elif message_type == 'navigate':
                await self.handle_navigation(data)
            # Handle 'new_tab' message - create new tab
            elif message_type == 'new_tab':
                await self.create_new_tab()
            elif self.message_router:
                await self.message_router.route(text_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Message error: {e}")

    async def send_frame(self, frame_base64: str) -> None:
        """Send frame data to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'frame',
            'data': frame_base64
        }))

    async def send_error(self, message: str) -> None:
        """Send error message to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    async def send_page_added(self, page_id: str) -> None:
        """Send page added notification to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'page_added',
            'page_id': page_id
        }))
    
    async def send_page_removed(self, page_id: str) -> None:
        """Send page removed notification to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'page_removed',
            'page_id': page_id
        }))
    
    async def send_pages_sync(self) -> None:
        """Send initial page list sync to WebSocket client."""
        if self.browser_manager:
            page_ids = self.browser_manager.get_all_page_ids()
            await self.send(text_data=json.dumps({
                'type': 'pages_sync',
                'page_ids': page_ids
            }))
    
    async def switch_active_page(self, page_id: str) -> None:
        """
        Switch the active page for streaming and input handling.
        Single Responsibility: This method coordinates updating all page-dependent components.
        
        Args:
            page_id: UUID string of the page to switch to
        """
        if not self.browser_manager:
            await self.send_error('Browser not initialized')
            return
        
        # Get the page instance
        page = self.browser_manager.get_page_by_id(page_id)
        if not page:
            await self.send_error(f'Page with ID {page_id} not found')
            return
        
        try:
            # Bring the page to front and make it active
            await page.bring_to_front()
            
            # Update all page-dependent components in one place
            if self.screenshot_streamer:
                self.screenshot_streamer.set_page(page)
            
            if self.mouse_controller:
                self.mouse_controller.page = page
            
            if self.keyboard_controller:
                self.keyboard_controller.page = page
            
            # Update the main page reference
            self.browser_manager.page = page
            
            # Send confirmation to frontend with current URL
            current_url = page.url
            await self.send(text_data=json.dumps({
                'type': 'page_switched',
                'page_id': page_id,
                'url': current_url
            }))
            
            print(f"[+] Switched to page: {page_id}")
        except Exception as e:
            print(f"Error switching page: {e}")
            await self.send_error(f'Error switching page: {str(e)}')
    
    async def handle_navigation(self, data: dict) -> None:
        """
        Handle navigation commands (back, forward, refresh, goto).
        
        Args:
            data: Navigation command data with 'action' and optional 'url'
        """
        if not self.browser_manager or not self.browser_manager.page:
            await self.send_error('Browser not initialized or no active page')
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
                    await self.send_error('URL required for goto action')
                    return
                await page.goto(url, wait_until='commit')
            else:
                await self.send_error(f'Unknown navigation action: {action}')
                return
            
            # Update address bar with current URL
            current_url = page.url
            await self.send(text_data=json.dumps({
                'type': 'url_changed',
                'url': current_url
            }))
            
            print(f"[+] Navigation: {action}")
        except Exception as e:
            print(f"Error in navigation: {e}")
            await self.send_error(f'Navigation error: {str(e)}')
    
    async def create_new_tab(self) -> None:
        """
        Create a new tab/page and navigate it to google.com.
        The page will be automatically tracked and switched to via page_added_callback.
        """
        if not self.browser_manager or not self.browser_manager.context:
            await self.send_error('Browser not initialized')
            return
        
        try:
            # Create a new page in the existing context
            # This will trigger the page_added_callback which will auto-switch to it
            new_page = await self.browser_manager.context.new_page()
            
            # Navigate to google.com
            await new_page.goto('https://www.google.com', wait_until='commit')
            
            print(f"[+] Created new tab and navigated to google.com")
        except Exception as e:
            print(f"Error creating new tab: {e}")
            await self.send_error(f'Error creating new tab: {str(e)}')

    async def start_streaming(self):
        """Start browser and begin streaming screenshots."""
        if self.streaming:
            return
        
        self.streaming = True
        
        try:
            # Create callback functions for page events
            # These are called from sync contexts (Playwright event handlers)
            # so we schedule the async operations using create_task
            def page_added_callback(page_id: str):
                """Synchronous wrapper that schedules async operations for new pages."""
                try:
                    loop = asyncio.get_running_loop()
                    # Send page_added notification
                    loop.create_task(self.send_page_added(page_id))
                    # Automatically switch to the new page
                    loop.create_task(self.switch_active_page(page_id))
                except RuntimeError:
                    # If no event loop is running, create a new one (shouldn't happen)
                    asyncio.create_task(self.send_page_added(page_id))
                    asyncio.create_task(self.switch_active_page(page_id))
            
            def page_removed_callback(page_id: str):
                """Synchronous wrapper that schedules async send_page_removed."""
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.send_page_removed(page_id))
                except RuntimeError:
                    # If no event loop is running, create a new one (shouldn't happen)
                    asyncio.create_task(self.send_page_removed(page_id))
            
            # Initialize browser manager with callbacks and launch browser
            self.browser_manager = BrowserManager(
                viewport_width=StreamConfig.CANVAS_WIDTH,
                viewport_height=StreamConfig.CANVAS_HEIGHT,
                page_added_callback=page_added_callback,
                page_removed_callback=page_removed_callback
            )
            # Launch browser - first page will be added via callback and auto-switched
            await self.browser_manager.launch(
                url=StreamConfig.BROWSER_URL,
                headless=StreamConfig.HEADLESS
            )
            
            # Send initial page list sync after browser launch if same 
            # browser was streamed from multiple clients then if user join 
            # late he gets all list of pages
            await self.send_pages_sync()
            
            # Start streaming - streamer will wait for page to be set via switch_active_page
            await self.screenshot_streamer.stream(
                send_callback=self.send_frame
            )
            
        except Exception as e:
            print(f"Error in streaming: {e}")
            await self.send_error(f'Streaming error: {str(e)}')
        finally:
            self.streaming = False
            if self.browser_manager:
                await self.browser_manager.cleanup()

