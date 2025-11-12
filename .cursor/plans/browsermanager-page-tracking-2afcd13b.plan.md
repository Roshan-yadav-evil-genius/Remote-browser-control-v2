<!-- 2afcd13b-15cf-4c1b-b127-fcb5d749761f 20b0af02-71c7-4e3a-905e-0c25216efe46 -->
# Single Responsibility Principle Analysis and Refactoring Plan

## Current SRP Violations Identified

### 1. **VideoStreamConsumer** - Multiple Responsibilities (CRITICAL)

**Current Responsibilities:**

- WebSocket connection management (connect/disconnect)
- Message routing and dispatching (receive method with multiple if/elif branches)
- Browser lifecycle management (start_streaming)
- Page switching coordination (switch_active_page)
- Navigation handling (handle_navigation)
- Tab management (create_new_tab, close_tab)
- WebSocket message sending (send_frame, send_error, send_page_added, send_page_removed, send_pages_sync)
- Component initialization and coordination
- Callback management for page events

**SRP Violation:** This class violates SRP by handling too many concerns. It should primarily coordinate, not implement all features.

### 2. **BrowserManager** - Minor Issues

**Current Responsibilities:**

- Browser/context/page lifecycle
- Page tracking with UUIDs
- Event listener setup
- Callback invocation

**Status:** Mostly compliant, but callback invocation could be extracted.

## Proposed Refactoring

### 1. Create `PageManager` class

**Responsibility:** Manage page operations (switch, create, close)

- `switch_active_page(page_id)` - Move from Consumer
- `create_new_tab()` - Move from Consumer  
- `close_tab(page_id)` - Move from Consumer
- Coordinate page updates across controllers/streamer

### 2. Create `NavigationManager` class

**Responsibility:** Handle browser navigation commands

- `handle_navigation(data)` - Move from Consumer
- Methods: back(), forward(), refresh(), goto(url)
- URL change notifications

### 3. Create `WebSocketMessageSender` class or use composition

**Responsibility:** Send WebSocket messages to frontend

- `send_frame()`, `send_error()`, `send_page_added()`, `send_page_removed()`, `send_pages_sync()`
- Centralize all WebSocket message formatting

### 4. Create `PageEventCoordinator` class

**Responsibility:** Coordinate page lifecycle events

- Handle page_added and page_removed callbacks
- Coordinate between BrowserManager and other components
- Manage auto-switching logic

### 5. Refactor `VideoStreamConsumer` to be a Facade

**New Responsibility:** Coordinate between managers, delegate to specialized classes

- Keep WebSocket connection management
- Delegate message routing to MessageRouter (already done for mouse/keyboard)
- Delegate page operations to PageManager
- Delegate navigation to NavigationManager
- Delegate message sending to WebSocketMessageSender

## Implementation Strategy

1. **Phase 1: Extract Message Sending**

- Create WebSocketMessageSender helper class
- Move all send_* methods to it
- Consumer uses it via composition

2. **Phase 2: Extract Page Management**

- Create PageManager class
- Move switch_active_page, create_new_tab, close_tab
- PageManager coordinates with controllers/streamer

3. **Phase 3: Extract Navigation**

- Create NavigationManager class
- Move handle_navigation method
- Handle URL change notifications

4. **Phase 4: Extract Event Coordination**

- Create PageEventCoordinator
- Handle page_added/page_removed callbacks
- Coordinate auto-switching

5. **Phase 5: Simplify Consumer**

- Consumer becomes a thin coordinator
- Routes messages to appropriate managers
- Maintains WebSocket connection lifecycle

## Benefits

- **Better Testability:** Each class has a single, testable responsibility
- **Easier Maintenance:** Changes to page management don't affect navigation logic
- **Clearer Code:** Each class has a clear, focused purpose
- **Better Reusability:** Managers can be reused in other contexts
- **Easier Debugging:** Issues are isolated to specific classes