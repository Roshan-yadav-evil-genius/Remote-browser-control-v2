const canvas = document.getElementById('videoCanvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('startBtn');
const statusDiv = document.getElementById('status');
const pagesListDiv = document.getElementById('pagesList');

// Canvas dimensions (internal resolution)
const CANVAS_WIDTH = 1920;
const CANVAS_HEIGHT = 1080;

// Set canvas internal size
canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

let ws = null;
let streaming = false;
let activePageIds = new Set(); // Track active page IDs
let currentPageId = null; // Track currently active page being streamed

// Throttle mousemove events to avoid overwhelming backend
let mousemoveThrottle = null;
const MOUSEMOVE_THROTTLE_MS = 16; // ~60fps for mouse movement

// Scale canvas to fit viewport while maintaining aspect ratio
function scaleCanvas() {
	const container = canvas.parentElement;
	const maxWidth = window.innerWidth - 100; // Leave some margin
	const maxHeight = window.innerHeight - 200; // Leave space for controls

	const aspectRatio = CANVAS_WIDTH / CANVAS_HEIGHT;
	let displayWidth = maxWidth;
	let displayHeight = displayWidth / aspectRatio;

	if (displayHeight > maxHeight) {
		displayHeight = maxHeight;
		displayWidth = displayHeight * aspectRatio;
	}

	canvas.style.width = displayWidth + 'px';
	canvas.style.height = displayHeight + 'px';
}
// Scale on load and resize
scaleCanvas();
window.addEventListener('resize', scaleCanvas);

// Map mouse button number to button name
function getButtonName(button) {
	const buttonMap = {
		0: 'left',
		1: 'middle',
		2: 'right'
	};
	return buttonMap[button] || 'left';
}

// Reusable coordinate mapping function
function mapCoordinates(clientX, clientY) {
	const rect = canvas.getBoundingClientRect();
	const clickX = clientX - rect.left;
	const clickY = clientY - rect.top;

	const scaleX = canvas.width / rect.width;
	const scaleY = canvas.height / rect.height;

	const x = Math.round(clickX * scaleX);
	const y = Math.round(clickY * scaleY);

	const boundedX = Math.max(0, Math.min(x, CANVAS_WIDTH - 1));
	const boundedY = Math.max(0, Math.min(y, CANVAS_HEIGHT - 1));

	return { x: boundedX, y: boundedY };
}

// Update pages display UI
function updatePagesDisplay() {
	if (activePageIds.size === 0) {
		pagesListDiv.textContent = 'None';
		pagesListDiv.innerHTML = '<span class="no-pages">None</span>';
	} else {
		const pageIdsArray = Array.from(activePageIds);
		pagesListDiv.innerHTML = pageIdsArray.map(pageId => {
			const isActive = pageId === currentPageId;
			const activeClass = isActive ? ' active' : '';
			return `<button class="page-badge${activeClass}" data-page-id="${pageId}" title="Page ID: ${pageId}">${pageId.substring(0, 8)}...</button>`;
		}).join(' ');
		
		// Add click event listeners to all page badges
		pagesListDiv.querySelectorAll('.page-badge').forEach(button => {
			button.addEventListener('click', function() {
				const pageId = this.getAttribute('data-page-id');
				if (pageId && ws && ws.readyState === WebSocket.OPEN) {
					ws.send(JSON.stringify({
						type: 'page_switch',
						page_id: pageId
					}));
				}
			});
		});
	}
}

// WebSocket connection
function connectWebSocket() {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const wsUrl = `${protocol}//${window.location.host}/ws/video/`;

	ws = new WebSocket(wsUrl);

	ws.onopen = function () {
		statusDiv.textContent = 'Connected';
		ws.send(JSON.stringify({ type: 'start' }));
		streaming = true;
		startBtn.disabled = true;
		startBtn.textContent = 'Streaming...';
		// Auto-focus canvas when streaming starts
		canvas.focus();
	};

	ws.onmessage = function (event) {
		const data = JSON.parse(event.data);

		if (data.type === 'frame') {
			const img = new Image();
			img.onload = function () {
				ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
			};
			img.src = 'data:image/jpeg;base64,' + data.data;
		} else if (data.type === 'error') {
			statusDiv.textContent = 'Error: ' + data.message;
			streaming = false;
			startBtn.disabled = false;
			startBtn.textContent = 'Start';
		} else if (data.type === 'page_added') {
			// Add page ID to tracking set
			if (data.page_id) {
				activePageIds.add(data.page_id);
				updatePagesDisplay();
			}
		} else if (data.type === 'page_removed') {
			// Remove page ID from tracking set
			if (data.page_id) {
				activePageIds.delete(data.page_id);
				updatePagesDisplay();
			}
		} else if (data.type === 'pages_sync') {
			// Initialize/sync all page IDs
			if (data.page_ids && Array.isArray(data.page_ids)) {
				activePageIds = new Set(data.page_ids);
			}
			updatePagesDisplay();
		} else if (data.type === 'page_switched') {
			// Update current page ID and refresh display
			if (data.page_id) {
				currentPageId = data.page_id;
				updatePagesDisplay();
			}
		}
	};

	ws.onerror = function (error) {
		statusDiv.textContent = 'WebSocket error';
		console.error('WebSocket error:', error);
	};

	ws.onclose = function () {
		statusDiv.textContent = 'Disconnected';
		streaming = false;
		startBtn.disabled = false;
		startBtn.textContent = 'Start';
		// Clear page tracking on disconnect
		activePageIds.clear();
		currentPageId = null;
		updatePagesDisplay();
	};
}

// Start streaming
startBtn.addEventListener('click', function () {
	if (!ws || ws.readyState !== WebSocket.OPEN) {
		// Reconnect if needed
		if (ws) {
			ws.close();
		}
		connectWebSocket();
	}
});

// Send mouse event to backend
function sendMouseEvent(type, event) {
	if (!streaming || !ws || ws.readyState !== WebSocket.OPEN) {
		return;
	}

	const coords = mapCoordinates(event.clientX, event.clientY);
	const message = {
		type: type,
		x: coords.x,
		y: coords.y
	};

	// Add button info for mouse events
	if (event.button !== undefined) {
		message.button = getButtonName(event.button);
	}

	// Add wheel delta for wheel events
	if (type === 'wheel') {
		message.deltaX = event.deltaX || 0;
		message.deltaY = event.deltaY || 0;
		message.deltaZ = event.deltaZ || 0;
	}

	ws.send(JSON.stringify(message));
}

// Prevent context menu on right click
canvas.addEventListener('contextmenu', function (event) {
	event.preventDefault();
	if (streaming) {
		sendMouseEvent('click', event);
	}
});

// Mouse move handler with throttling
canvas.addEventListener('mousemove', function (event) {
	if (!streaming || !ws || ws.readyState !== WebSocket.OPEN) {
		return;
	}

	// Throttle mousemove events
	if (mousemoveThrottle) {
		clearTimeout(mousemoveThrottle);
	}

	mousemoveThrottle = setTimeout(function () {
		sendMouseEvent('mousemove', event);
	}, MOUSEMOVE_THROTTLE_MS);
});

// Mouse down handler
canvas.addEventListener('mousedown', function (event) {
	sendMouseEvent('mousedown', event);
});

// Mouse up handler
canvas.addEventListener('mouseup', function (event) {
	sendMouseEvent('mouseup', event);
});

// Click handler (for backward compatibility)
canvas.addEventListener('click', function (event) {
	const coords = mapCoordinates(event.clientX, event.clientY);
	sendMouseEvent('click', event);
	statusDiv.textContent = `Click at (${coords.x}, ${coords.y})`;
});

// Wheel/scroll handler
canvas.addEventListener('wheel', function (event) {
	event.preventDefault(); // Prevent page scroll
	sendMouseEvent('wheel', event);
});

// Mouse leave handler (optional - can be used to stop mouse tracking)
canvas.addEventListener('mouseleave', function (event) {
	// Clear any pending mousemove events
	if (mousemoveThrottle) {
		clearTimeout(mousemoveThrottle);
		mousemoveThrottle = null;
	}
});

// Send keyboard event to backend
function sendKeyboardEvent(type, event) {
	if (!streaming || !ws || ws.readyState !== WebSocket.OPEN) {
		return;
	}

	// Only send if canvas is focused
	if (document.activeElement !== canvas) {
		return;
	}

	const message = {
		type: type,
		key: event.key,
		code: event.code,
		ctrlKey: event.ctrlKey || false,
		altKey: event.altKey || false,
		shiftKey: event.shiftKey || false,
		metaKey: event.metaKey || false
	};

	// Add repeat property for keydown events
	if (type === 'keydown') {
		message.repeat = event.repeat || false;
	}

	ws.send(JSON.stringify(message));
}

// Keyboard event handlers
canvas.addEventListener('keydown', function (event) {
	// Prevent common browser shortcuts
	if (event.ctrlKey || event.metaKey) {
		const key = event.key.toLowerCase();
		// Prevent Ctrl+R (refresh), Ctrl+W (close), Ctrl+N (new window), etc.
		if (key === 'r' || key === 'w' || key === 'n' || key === 't') {
			event.preventDefault();
			event.stopPropagation();
		}
	}

	// Prevent default browser behavior for all keys when canvas is focused
	event.preventDefault();
	event.stopPropagation();

	sendKeyboardEvent('keydown', event);
});

canvas.addEventListener('keyup', function (event) {
	// Prevent default browser behavior for all keys when canvas is focused
	event.preventDefault();
	event.stopPropagation();

	sendKeyboardEvent('keyup', event);
});

