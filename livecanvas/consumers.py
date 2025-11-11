"""WebSocket consumer for video streaming."""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .browser_manager import BrowserManager
from .screenshot_streamer import ScreenshotStreamer


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that handles video streaming via browser screenshots."""
    
    BROWSER_URL = 'https://shawon9324.github.io/apps/keytester/'
    CANVAS_WIDTH = 1920
    CANVAS_HEIGHT = 1080
    STREAMING_FPS = 15.0
    
    async def connect(self):
        await self.accept()
        self.streaming = False
        self.browser_manager: BrowserManager = None
        self.screenshot_streamer: ScreenshotStreamer = None
        self.streaming_task = None

    async def disconnect(self, close_code):
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
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'start':
                if not self.streaming:
                    self.streaming_task = asyncio.create_task(self.start_streaming())
            elif message_type == 'click':
                await self.handle_click(data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")

    async def handle_click(self, data: dict) -> None:
        """Handle click events from client."""
        x = data.get('x')
        y = data.get('y')
        print(f"Click received: x={x}, y={y}")
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            print(f"Clicking in browser at: ({browser_x}, {browser_y})")
            try:
                await self.browser_manager.click(browser_x, browser_y)
            except Exception as e:
                print(f"Error clicking in browser: {e}")

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

    async def start_streaming(self):
        """Start browser and begin streaming screenshots."""
        if self.streaming:
            return
        
        self.streaming = True
        
        try:
            # Initialize browser manager and launch browser
            self.browser_manager = BrowserManager(
                viewport_width=self.CANVAS_WIDTH,
                viewport_height=self.CANVAS_HEIGHT
            )
            page = await self.browser_manager.launch(
                url=self.BROWSER_URL,
                headless=False
            )
            
            # Initialize screenshot streamer
            self.screenshot_streamer = ScreenshotStreamer(
                page=page,
                fps=self.STREAMING_FPS
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

