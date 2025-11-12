"""WebSocket message sending functionality."""
import json
from typing import Callable, Awaitable


class WebSocketMessageSender:
    """Handles sending WebSocket messages to frontend clients."""
    
    def __init__(self, send_func: Callable[[str], Awaitable[None]]):
        """
        Initialize message sender.
        
        Args:
            send_func: Async function to send text data via WebSocket
        """
        self.send = send_func
    
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
    
    async def send_pages_sync(self, page_ids: list[str]) -> None:
        """Send initial page list sync to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'pages_sync',
            'page_ids': page_ids
        }))
    
    async def send_page_switched(self, page_id: str, url: str) -> None:
        """Send page switched notification to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'page_switched',
            'page_id': page_id,
            'url': url
        }))
    
    async def send_url_changed(self, url: str) -> None:
        """Send URL changed notification to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'url_changed',
            'url': url
        }))

