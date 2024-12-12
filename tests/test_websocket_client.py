import asyncio
import websockets
import json
import base64
import numpy as np
import cv2
from datetime import datetime

async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/surveillance"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to server")

        # Send init message
        init_message = {
            'type': 'init',
            'client_id': f'test_client_{datetime.now().timestamp()}',
            'capabilities': ['camera', 'ar']
        }
        await websocket.send(json.dumps(init_message))
        response = await websocket.recv()
        print(f"Init response: {response}")

        # Create a test image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_image, 'Test Frame', (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Encode image
        _, buffer = cv2.imencode('.jpg', test_image)
        frame_bytes = base64.b64encode(buffer).decode('utf-8')

        # Send frame
        frame_message = {
            'type': 'frame',
            'metadata': {
                'format': 'yuv420',
                'width': 640,
                'height': 480,
                'planes': [{
                    'bytes_per_row': 640,
                    'bytes_per_pixel': 1,
                    'width': 640,
                    'height': 480
                }],
                'timestamp': datetime.now().isoformat(),
                'client_id': 'test_client'
            },
            'frame_data': frame_bytes
        }
        
        print("Sending frame...")
        await websocket.send(json.dumps(frame_message))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Server response: {response}")

        # Send ping to keep connection alive
        ping_message = {'type': 'ping'}
        await websocket.send(json.dumps(ping_message))
        pong = await websocket.recv()
        print(f"Ping response: {pong}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection()) 