"""Manager classes for browser operations, page management, and message routing."""
from .browser_manager import BrowserManager
from .page_manager import PageManager
from .navigation_manager import NavigationManager
from .page_event_coordinator import PageEventCoordinator
from .websocket_message_sender import WebSocketMessageSender
from .message_router import MessageRouter
from .interaction_manager import InteractionManager

__all__ = [
    'BrowserManager',
    'PageManager',
    'NavigationManager',
    'PageEventCoordinator',
    'WebSocketMessageSender',
    'MessageRouter',
    'InteractionManager',
]

