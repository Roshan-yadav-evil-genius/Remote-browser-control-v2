"""Configuration management for video streaming."""
from typing import List


class StreamConfig:
    """Centralized configuration for video streaming."""
    
    # Testing URLs
    TESTING_URLS: List[str] = [
        "https://shawon9324.github.io/apps/keytester/",
        "https://cuberto.com/blog/cuberto-mouse-follower/",
        "https://www.w3schools.com/tags/att_a_target.asp"
    ]
    
    # Browser configuration
    BROWSER_URL: str = TESTING_URLS[2]
    CANVAS_WIDTH: int = 1920
    CANVAS_HEIGHT: int = 1080
    STREAMING_FPS: float = 15.0
    
    # Browser settings
    HEADLESS: bool = False

