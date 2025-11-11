"""WebSocket consumer for video streaming."""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .browser_manager import BrowserManager
from .screenshot_streamer import ScreenshotStreamer


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer that handles video streaming via browser screenshots."""
    TESTING_URLS=["https://shawon9324.github.io/apps/keytester/","https://cuberto.com/blog/cuberto-mouse-follower/"]
    BROWSER_URL = TESTING_URLS[0]
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
            elif message_type == 'mousemove':
                await self.handle_mousemove(data)
            elif message_type == 'mousedown':
                await self.handle_mousedown(data)
            elif message_type == 'mouseup':
                await self.handle_mouseup(data)
            elif message_type == 'click':
                await self.handle_click(data)
            elif message_type == 'wheel':
                await self.handle_wheel(data)
            elif message_type == 'keydown':
                await self.handle_keydown(data)
            elif message_type == 'keyup':
                await self.handle_keyup(data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")

    async def handle_mousemove(self, data: dict) -> None:
        """Handle mouse movement events from client."""
        x = data.get('x')
        y = data.get('y')
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            try:
                await self.browser_manager.move_mouse(browser_x, browser_y)
            except Exception as e:
                print(f"Error moving mouse in browser: {e}")
    
    async def handle_mousedown(self, data: dict) -> None:
        """Handle mouse down events from client."""
        x = data.get('x')
        y = data.get('y')
        button = data.get('button', 'left')
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            print(f"Mouse down in browser at: ({browser_x}, {browser_y}), button: {button}")
            try:
                await self.browser_manager.mouse_down(browser_x, browser_y, button)
            except Exception as e:
                print(f"Error with mouse down in browser: {e}")
    
    async def handle_mouseup(self, data: dict) -> None:
        """Handle mouse up events from client."""
        x = data.get('x')
        y = data.get('y')
        button = data.get('button', 'left')
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            print(f"Mouse up in browser at: ({browser_x}, {browser_y}), button: {button}")
            try:
                await self.browser_manager.mouse_up(browser_x, browser_y, button)
            except Exception as e:
                print(f"Error with mouse up in browser: {e}")
    
    async def handle_click(self, data: dict) -> None:
        """Handle click events from client."""
        x = data.get('x')
        y = data.get('y')
        button = data.get('button', 'left')
        print(f"Click received: x={x}, y={y}, button={button}")
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            print(f"Clicking in browser at: ({browser_x}, {browser_y}), button: {button}")
            try:
                await self.browser_manager.click(browser_x, browser_y, button)
            except Exception as e:
                print(f"Error clicking in browser: {e}")
    
    async def handle_wheel(self, data: dict) -> None:
        """Handle wheel/scroll events from client."""
        x = data.get('x')
        y = data.get('y')
        delta_x = data.get('deltaX', 0)
        delta_y = data.get('deltaY', 0)
        
        if x is not None and y is not None and self.browser_manager:
            browser_x = int(x)
            browser_y = int(y)
            print(f"Scrolling in browser at: ({browser_x}, {browser_y}), delta: ({delta_x}, {delta_y})")
            try:
                await self.browser_manager.scroll(browser_x, browser_y, delta_x, delta_y)
            except Exception as e:
                print(f"Error scrolling in browser: {e}")
    
    async def handle_keydown(self, data: dict) -> None:
        """Handle key down events from client."""
        key = data.get('key')
        code = data.get('code')
        ctrl_key = data.get('ctrlKey', False)
        alt_key = data.get('altKey', False)
        shift_key = data.get('shiftKey', False)
        meta_key = data.get('metaKey', False)
        repeat = data.get('repeat', False)
        
        if not key or not self.browser_manager:
            return
        
        # Build modifiers list
        modifiers = []
        if ctrl_key:
            modifiers.append('Control')
        if alt_key:
            modifiers.append('Alt')
        if shift_key:
            modifiers.append('Shift')
        if meta_key:
            modifiers.append('Meta')
        
        # Skip if this is a repeat event for modifier keys (to avoid spam)
        if repeat and key in ['Control', 'Alt', 'Shift', 'Meta']:
            return
        
        print(f"Key down: {key}, code: {code}, modifiers: {modifiers}, repeat: {repeat}")
        try:
            await self.browser_manager.key_down(key, code, modifiers if modifiers else None)
        except Exception as e:
            print(f"Error with key down in browser: {e}")
    
    async def handle_keyup(self, data: dict) -> None:
        """Handle key up events from client."""
        key = data.get('key')
        code = data.get('code')
        ctrl_key = data.get('ctrlKey', False)
        alt_key = data.get('altKey', False)
        shift_key = data.get('shiftKey', False)
        meta_key = data.get('metaKey', False)
        
        if not key or not self.browser_manager:
            return
        
        # Build modifiers list
        modifiers = []
        if ctrl_key:
            modifiers.append('Control')
        if alt_key:
            modifiers.append('Alt')
        if shift_key:
            modifiers.append('Shift')
        if meta_key:
            modifiers.append('Meta')
        
        print(f"Key up: {key}, code: {code}, modifiers: {modifiers}")
        try:
            await self.browser_manager.key_up(key, code, modifiers if modifiers else None)
        except Exception as e:
            print(f"Error with key up in browser: {e}")

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

