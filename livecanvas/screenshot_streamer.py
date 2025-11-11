"""Screenshot capture and streaming functionality."""
import base64
import asyncio
from typing import Awaitable, Callable, Optional
from playwright.async_api import Page


class ScreenshotStreamer:
    """Handles screenshot capture and encoding for streaming."""
    
    def __init__(self, page: Page, fps: float = 15.0, quality: int = 85):
        """
        Initialize screenshot streamer.
        
        Args:
            page: Playwright Page instance
            fps: Frames per second for streaming
            quality: JPEG quality (1-100)
        """
        self.page = page
        self.fps = fps
        self.quality = quality
        self.frame_delay = 1.0 / fps
        self.streaming = False
    
    async def capture_screenshot(self) -> str:
        """
        Capture screenshot and encode as base64 string.
        
        Returns:
            Base64-encoded JPEG image string
        """
        screenshot_bytes = await self.page.screenshot(
            type='jpeg',
            quality=self.quality
        )
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def stream(
        self,
        send_callback: Callable[[str], Awaitable[None]],
        stop_event: Optional[asyncio.Event] = None
    ) -> None:
        """
        Stream screenshots continuously.
        
        Args:
            send_callback: Async function to send frame data
            stop_event: Optional event to signal stopping
        """
        self.streaming = True
        
        try:
            while self.streaming:
                if stop_event and stop_event.is_set():
                    break
                
                if not self.page:
                    break
                
                frame_base64 = await self.capture_screenshot()
                await send_callback(frame_base64)
                
                await asyncio.sleep(self.frame_delay)
        except asyncio.CancelledError:
            print("Screenshot streaming cancelled")
            raise
        finally:
            self.streaming = False
    
    def stop(self) -> None:
        """Stop streaming."""
        self.streaming = False

