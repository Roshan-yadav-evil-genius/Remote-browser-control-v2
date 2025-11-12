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
from .websocket_message_sender import WebSocketMessageSender
from .page_manager import PageManager
from .navigation_manager import NavigationManager
from .page_event_coordinator import PageEventCoordinator


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that coordinates video streaming via browser screenshots.
    
    Acts as a Facade that delegates to specialized managers:
    - WebSocketMessageSender: Message sending
    - PageManager: Page operations (switch, create, close)
    - NavigationManager: Browser navigation
    - PageEventCoordinator: Page lifecycle events
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        self.streaming = False
        self.browser_manager: BrowserManager = None
        self.streaming_task = None
        
        # Initialize WebSocket message sender
        self.message_sender = WebSocketMessageSender(self.send)
        
        # Initialize controllers and streamer without pages (lazy initialization)
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        
        # Initialize screenshot streamer without page
        self.screenshot_streamer = ScreenshotStreamer(
            fps=StreamConfig.STREAMING_FPS
        )
        
        # Initialize managers (will be fully initialized after browser_manager is created)
        self.page_manager: PageManager = None
        self.navigation_manager: NavigationManager = None
        self.page_event_coordinator: PageEventCoordinator = None
        
        # Initialize message router with handlers
        self.message_router = MessageRouter(
            mouse_handler=MouseHandler(self.mouse_controller),
            keyboard_handler=KeyboardHandler(self.keyboard_controller),
            start_callback=None  # Already handled
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
        """Handle incoming WebSocket messages and delegate to appropriate managers."""
        print(f"Received message: {text_data}")
        try:
            validator = MessageValidator()
            data = validator.validate_json(text_data)
            message_type = validator.validate_message_type(data)
            
            # Handle 'start' message before router is initialized
            if message_type == 'start' and not self.streaming:
                self.streaming_task = asyncio.create_task(self.start_streaming())
            # Handle 'page_switch' message - delegate to PageManager
            elif message_type == 'page_switch':
                if 'page_id' in data:
                    if self.page_manager:
                        await self.page_manager.switch_active_page(data['page_id'])
                    else:
                        await self.message_sender.send_error('Page manager not initialized')
                else:
                    await self.message_sender.send_error('page_switch message missing page_id')
            # Handle 'navigate' message - delegate to NavigationManager
            elif message_type == 'navigate':
                if self.navigation_manager:
                    await self.navigation_manager.handle_navigation(data)
                else:
                    await self.message_sender.send_error('Navigation manager not initialized')
            # Handle 'new_tab' message - delegate to PageManager
            elif message_type == 'new_tab':
                if self.page_manager:
                    await self.page_manager.create_new_tab()
                else:
                    await self.message_sender.send_error('Page manager not initialized')
            # Handle 'close_tab' message - delegate to PageManager
            elif message_type == 'close_tab':
                if 'page_id' in data:
                    if self.page_manager:
                        await self.page_manager.close_tab(data['page_id'])
                    else:
                        await self.message_sender.send_error('Page manager not initialized')
                else:
                    await self.message_sender.send_error('close_tab message missing page_id')
            elif self.message_router:
                await self.message_router.route(text_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Message error: {e}")


    async def start_streaming(self):
        """Start browser and begin streaming screenshots."""
        if self.streaming:
            return
        
        self.streaming = True
        
        try:
            # Initialize browser manager first (without callbacks yet)
            self.browser_manager = BrowserManager(
                viewport_width=StreamConfig.CANVAS_WIDTH,
                viewport_height=StreamConfig.CANVAS_HEIGHT
            )
            
            # Initialize managers that depend on browser_manager
            self.page_manager = PageManager(
                browser_manager=self.browser_manager,
                screenshot_streamer=self.screenshot_streamer,
                mouse_controller=self.mouse_controller,
                keyboard_controller=self.keyboard_controller,
                message_sender=self.message_sender
            )
            
            self.navigation_manager = NavigationManager(
                browser_manager=self.browser_manager,
                message_sender=self.message_sender
            )
            
            self.page_event_coordinator = PageEventCoordinator(
                page_manager=self.page_manager,
                message_sender=self.message_sender
            )
            
            # Set up callbacks for page events
            page_added_callback = self.page_event_coordinator.create_page_added_callback()
            page_removed_callback = self.page_event_coordinator.create_page_removed_callback()
            
            # Update browser manager with callbacks
            self.browser_manager.page_added_callback = page_added_callback
            self.browser_manager.page_removed_callback = page_removed_callback
            
            # Launch browser - first page will be added via callback and auto-switched
            await self.browser_manager.launch(
                url=StreamConfig.BROWSER_URL,
                headless=StreamConfig.HEADLESS
            )
            
            # Send initial page list sync after browser launch if same 
            # browser was streamed from multiple clients then if user join 
            # late he gets all list of pages
            page_ids = self.browser_manager.get_all_page_ids()
            await self.message_sender.send_pages_sync(page_ids)
            
            # Start streaming - streamer will wait for page to be set via switch_active_page
            await self.screenshot_streamer.stream(
                send_callback=self.message_sender.send_frame
            )
            
        except Exception as e:
            print(f"Error in streaming: {e}")
            await self.message_sender.send_error(f'Streaming error: {str(e)}')
        finally:
            self.streaming = False
            if self.browser_manager:
                await self.browser_manager.cleanup()

