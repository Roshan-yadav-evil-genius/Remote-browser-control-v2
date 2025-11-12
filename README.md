✦ The codebase utilizes several design patterns for a decoupled architecture. The primary one is a variation of Model-View-Controller (MVC). Here's a breakdown:

   - Facade: VideoStreamConsumer simplifies the entry point to the system.
   - Strategy: MessageRouter uses different Handler objects to process various message types.
   - Adapter: Handler classes adapt WebSocket data for the Controller classes.
   - Command: MessageRouter maps message types to handler methods.
   - Dependency Injection: VideoStreamConsumer dynamically creates and injects dependencies.
   - Data Mapper: KeyMapper and ButtonMapper translate data between client and server formats.
   - Lazy Initialization: Resources are allocated only when a 'start' command is received.
   - Callback: ScreenshotStreamer uses a callback to send frames, decoupling frame generation from the WebSocket.

Execution Command:

daphne -p 7979 livecanvas.asgi:application
