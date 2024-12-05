import pytest
import asyncio
import time
import numpy as np
from app.services.video_processing import VideoProcessingService
from app.services.ar_processing import ARProcessingService
from app.models.detection import DetectionResult, ConnectionStats
from app.core.config import settings

class TestPerformance:
    @pytest.fixture
    async def video_processor(self):
        processor = VideoProcessingService()
        yield processor
        # Cleanup
        await processor.cleanup()

    @pytest.fixture
    def sample_frame(self):
        # Create a test image with known objects
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        # Add test patterns that YOLO should detect
        return img

    async def test_processing_latency(self, video_processor, sample_frame):
        latencies = []
        for _ in range(100):  # Test with 100 frames
            start_time = time.time()
            results = await video_processor.process_frame(sample_frame, "test_client")
            latency = time.time() - start_time
            latencies.append(latency)
        
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        assert avg_latency < 0.1  # Average latency should be under 100ms
        assert p95_latency < 0.2  # 95th percentile should be under 200ms

    async def test_frame_rate_stability(self, video_processor, sample_frame):
        frame_times = []
        last_time = time.time()
        
        for _ in range(300):  # Test for 10 seconds at 30 FPS
            results = await video_processor.process_frame(sample_frame, "test_client")
            current_time = time.time()
            frame_times.append(current_time - last_time)
            last_time = current_time
            await asyncio.sleep(1/settings.MAX_FPS)
        
        frame_rate_variance = np.var(frame_times)
        assert frame_rate_variance < 0.001  # Frame timing should be stable

    async def test_bandwidth_usage(self, video_processor, sample_frame):
        stats = ConnectionStats(client_id="test_client")
        total_bytes = 0
        
        for _ in range(100):
            results = await video_processor.process_frame(sample_frame, "test_client")
            message_size = len(str(results))  # Approximate network payload
            total_bytes += message_size
            stats.update_bandwidth(message_size)
        
        avg_bandwidth = total_bytes / 100  # Average bytes per frame
        assert avg_bandwidth < 10000  # Should be under 10KB per frame

    async def test_detection_accuracy(self, video_processor):
        # Test with known images and verify detection accuracy
        test_cases = [
            {
                "image": "test_data/person.jpg",
                "expected": [
                    {"label": "person", "confidence_min": 0.8},
                    {"label": "face", "confidence_min": 0.9}
                ]
            },
            # Add more test cases
        ]
        
        for test_case in test_cases:
            results = await video_processor.process_frame(
                test_case["image"], 
                "test_client"
            )
            
            for expected in test_case["expected"]:
                matching_detection = next(
                    (r for r in results if r.label == expected["label"]), 
                    None
                )
                assert matching_detection is not None
                assert matching_detection.confidence >= expected["confidence_min"] 