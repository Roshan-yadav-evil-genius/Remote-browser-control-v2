import json
import base64
import cv2
import asyncio
from pathlib import Path
from channels.generic.websocket import AsyncWebsocketConsumer


class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.streaming = False
        self.click_coords = None
        self.video_path = Path("/home/roshan/main/TheOneEye/POC/websocketstreaming/video.mp4")
        self.cap = None
        self.streaming_task = None

    async def disconnect(self, close_code):
        self.streaming = False
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
        if self.cap is not None:
            self.cap.release()

    async def receive(self, text_data):
        print(f"Received message: {text_data}")
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'start':
                # Start streaming in background task so it doesn't block receive()
                if not self.streaming:
                    self.streaming_task = asyncio.create_task(self.start_streaming())
            elif message_type == 'click':
                x = data.get('x')
                y = data.get('y')
                print(f"Click received: x={x}, y={y}")
                if x is not None and y is not None:
                    self.click_coords = (int(x), int(y))
                    print(f"Click coordinates set to: {self.click_coords}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")

    async def start_streaming(self):
        if self.streaming:
            return
        
        self.streaming = True
        
        # Open video file
        if not self.video_path.exists():
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Video file not found'
            }))
            self.streaming = False
            return

        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to open video file'
            }))
            self.streaming = False
            return

        # Stream frames at ~15 FPS
        frame_delay = 1.0 / 15.0
        canvas_width = 640
        canvas_height = 480
        
        try:
            while self.streaming:
                ret, frame = self.cap.read()
                
                if not ret:
                    # Loop video by resetting to beginning
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                # Resize frame to match canvas dimensions
                frame = cv2.resize(frame, (canvas_width, canvas_height))

                # Overlay red dot if click coordinates exist
                if self.click_coords:
                    x, y = self.click_coords
                    # Ensure coordinates are within frame bounds
                    x = max(0, min(x, canvas_width - 1))
                    y = max(0, min(y, canvas_height - 1))
                    # Draw red circle at click position (BGR format: (0, 0, 255) = red)
                    cv2.circle(frame, (x, y), 15, (0, 0, 255), -1)  # Red filled circle, larger radius
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Send frame to client
                await self.send(text_data=json.dumps({
                    'type': 'frame',
                    'data': frame_base64
                }))
                
                await asyncio.sleep(frame_delay)
        except asyncio.CancelledError:
            print("Streaming task cancelled")
            raise
        except Exception as e:
            print(f"Error in streaming loop: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Streaming error: {str(e)}'
            }))
        finally:
            self.streaming = False
            if self.cap is not None:
                self.cap.release()
                self.cap = None

