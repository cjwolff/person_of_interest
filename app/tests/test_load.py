import asyncio
import websockets
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from ..core.config import settings

async def simulate_client(client_id: int, duration: int = 60):
    uri = f"ws://localhost:8000/ws/surveillance"
    metrics = {
        "latencies": [],
        "dropped_frames": 0,
        "connection_errors": 0
    }
    
    try:
        async with websockets.connect(uri) as websocket:
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                # Send frame
                frame_start = time.time()
                await websocket.send(json.dumps({
                    "type": "frame",
                    "data": "base64_encoded_test_frame",
                    "timestamp": frame_start
                }))
                
                # Receive response
                response = await websocket.recv()
                latency = time.time() - frame_start
                metrics["latencies"].append(latency)
                
                # Check for dropped frames
                if latency > 1.0/settings.MAX_FPS:
                    metrics["dropped_frames"] += 1
                
                frame_count += 1
                await asyncio.sleep(1/settings.MAX_FPS)
                
    except Exception as e:
        metrics["connection_errors"] += 1
        print(f"Client {client_id} error: {e}")
    
    return metrics

async def run_load_test(num_clients: int = 50, duration: int = 60):
    # Run multiple clients simultaneously
    tasks = [simulate_client(i, duration) for i in range(num_clients)]
    results = await asyncio.gather(*tasks)
    
    # Aggregate metrics
    all_latencies = []
    total_dropped_frames = 0
    total_errors = 0
    
    for metrics in results:
        all_latencies.extend(metrics["latencies"])
        total_dropped_frames += metrics["dropped_frames"]
        total_errors += metrics["connection_errors"]
    
    # Calculate statistics
    stats = {
        "avg_latency": statistics.mean(all_latencies),
        "p95_latency": statistics.quantiles(all_latencies, n=20)[18],  # 95th percentile
        "dropped_frames": total_dropped_frames,
        "connection_errors": total_errors,
        "total_clients": num_clients
    }
    
    # Print results
    print("\nLoad Test Results:")
    print(f"Average Latency: {stats['avg_latency']*1000:.2f}ms")
    print(f"95th Percentile Latency: {stats['p95_latency']*1000:.2f}ms")
    print(f"Dropped Frames: {stats['dropped_frames']}")
    print(f"Connection Errors: {stats['connection_errors']}")
    
    # Assert performance requirements
    assert stats["avg_latency"] < 0.1  # Average latency under 100ms
    assert stats["p95_latency"] < 0.2  # 95th percentile under 200ms
    assert stats["dropped_frames"] / (num_clients * duration * settings.MAX_FPS) < 0.01  # Less than 1% dropped frames
    assert stats["connection_errors"] == 0  # No connection errors

if __name__ == "__main__":
    asyncio.run(run_load_test()) 