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
        self.screenshot_streamer: ScreenshotStreamer = None
        self.mouse_controller: MouseController = None
        self.keyboard_controller: KeyboardController = None
        self.message_router: MessageRouter = None
        self.streaming_task = None

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
            if self.message_router:
                await self.message_router.route(text_data)
            else:
                # Handle 'start' message before router is initialized
                validator = MessageValidator()
                data = validator.validate_json(text_data)
                message_type = validator.validate_message_type(data)
                if message_type == 'start' and not self.streaming:
                    self.streaming_task = asyncio.create_task(self.start_streaming())
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
                """Synchronous wrapper that schedules async send_page_added."""
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.send_page_added(page_id))
                except RuntimeError:
                    # If no event loop is running, create a new one (shouldn't happen)
                    asyncio.create_task(self.send_page_added(page_id))
            
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
            page = await self.browser_manager.launch(
                url=StreamConfig.BROWSER_URL,
                headless=StreamConfig.HEADLESS
            )
            
            # Send initial page list sync after browser launch if same 
            # browser was streamed fro multipel clients then if user join 
            # late he gett all list of pages

            await self.send_pages_sync()
            
            # Initialize controllers
            self.mouse_controller = MouseController(page)
            self.keyboard_controller = KeyboardController(page)
            
            # Initialize event handlers
            mouse_handler = MouseHandler(self.mouse_controller)
            keyboard_handler = KeyboardHandler(self.keyboard_controller)
            
            # Initialize message router
            self.message_router = MessageRouter(
                mouse_handler=mouse_handler,
                keyboard_handler=keyboard_handler,
                start_callback=None  # Already handled
            )
            
            # Initialize screenshot streamer
            self.screenshot_streamer = ScreenshotStreamer(
                page=page,
                fps=StreamConfig.STREAMING_FPS
            )
            
            # Start streaming
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

