from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from ....services.video_processing import VideoProcessingService
from ....services.ar_processing import ARProcessingService
from ....core.deps import get_current_user
from ....models.detection import ConnectionStats
import json
import asyncio
import time

router = APIRouter()
video_processor = VideoProcessingService()
ar_processor = ARProcessingService()

@router.websocket("/ws/surveillance")
async def surveillance_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user)
):
    await websocket.accept()
    client_id = str(user.id)
    connection_stats = ConnectionStats(client_id=client_id)
    
    try:
        # Create result queue for this client
        video_processor.result_queues[client_id] = asyncio.Queue()
        
        # Start result sender task
        result_sender = asyncio.create_task(
            send_results(websocket, video_processor.result_queues[client_id], connection_stats)
        )
        
        # Start heartbeat task
        heartbeat = asyncio.create_task(
            send_heartbeat(websocket, settings.WS_HEARTBEAT_INTERVAL)
        )
        
        # Handle incoming frames
        async for message in websocket.iter_json():
            start_time = time.time()
            
            if message["type"] == "frame":
                await video_processor.processing_queue.put(
                    (message["data"], client_id)
                )
                connection_stats.update_latency(time.time() - start_time)
                
            elif message["type"] == "ar_frame":
                ar_data = await ar_processor.process_frame(
                    frame_data=message["data"],
                    detections=message.get("detections", []),
                    device_pose=message["device_pose"]
                )
                await websocket.send_json({
                    "type": "ar_update",
                    "data": ar_data.dict()
                })
                
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected normally")
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Cleanup
        if client_id in video_processor.result_queues:
            del video_processor.result_queues[client_id]
        result_sender.cancel()
        heartbeat.cancel()
        await websocket.close()
        print(f"Connection stats for {client_id}: {connection_stats.get_stats()}")

async def send_results(
    websocket: WebSocket, 
    result_queue: asyncio.Queue,
    stats: ConnectionStats
):
    try:
        while True:
            results = await result_queue.get()
            start_time = time.time()
            await websocket.send_json({
                "type": "detection_results",
                "data": [result.dict() for result in results],
                "timestamp": start_time
            })
            stats.update_bandwidth(len(str(results)))
    except asyncio.CancelledError:
        pass

async def send_heartbeat(websocket: WebSocket, interval: int):
    try:
        while True:
            await asyncio.sleep(interval)
            await websocket.send_json({"type": "heartbeat"})
    except asyncio.CancelledError:
        pass 