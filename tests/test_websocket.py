import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from app.main import app
import asyncio
from unittest.mock import AsyncMock, patch
from app.core.websocket import WebSocketManager

@pytest.mark.asyncio
async def test_websocket_connection():
    # Mock services
    mock_video_processor = AsyncMock()
    mock_ar_service = AsyncMock()
    mock_behavior_analyzer = AsyncMock()
    mock_geofencing = AsyncMock()
    
    # Set up mock return values
    mock_video_processor._bytes_to_frame.return_value = b"processed_frame"
    mock_video_processor.preprocess_frame.return_value = (b"processed_frame", {})
    mock_ar_service.process_frame.return_value = {"objects": []}
    mock_behavior_analyzer.analyze_behavior.return_value = {}
    mock_geofencing.update_client_location.return_value = []

    # Mock database session
    mock_db = AsyncMock()
    
    with patch('app.api.websocket_routes.video_processor', mock_video_processor), \
         patch('app.api.websocket_routes.ar_service', mock_ar_service), \
         patch('app.api.websocket_routes.behavior_analyzer', mock_behavior_analyzer), \
         patch('app.api.websocket_routes.geofencing', mock_geofencing), \
         patch('app.api.websocket_routes.get_db', return_value=mock_db):
        
        client = TestClient(app)
        with client.websocket_connect("/ws/surveillance") as websocket:
            # Send test data
            test_frame = b"test_frame_data"
            test_metadata = {
                "pose": {"x": 0, "y": 0, "z": 0},
                "location": {"lat": 0, "lng": 0}
            }
            
            websocket.send_bytes(test_frame)
            websocket.send_json(test_metadata)
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Receive response
            response = websocket.receive_json()
            
            # Basic assertions
            assert "ar_data" in response
            assert "metadata" in response
            assert "behavior_analysis" in response
            assert "geofence_events" in response

            # Verify mocks were called
            mock_video_processor._bytes_to_frame.assert_called_once()
            mock_video_processor.preprocess_frame.assert_called_once()
            mock_ar_service.process_frame.assert_called_once()
            mock_behavior_analyzer.analyze_behavior.assert_called_once()
            mock_geofencing.update_client_location.assert_called_once()