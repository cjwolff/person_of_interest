import pytest
import asyncio
import uvicorn
from fastapi.testclient import TestClient
from app.main import app
from app.core.websocket import WebSocketManager
from test_websocket_client import test_websocket_connection
import logging

@pytest.fixture
async def test_app():
    client = TestClient(app)
    yield client

@pytest.mark.asyncio
async def test_websocket_communication():
    # Start server in background
    server_task = asyncio.create_task(
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
    )
    
    try:
        # Wait for server to start
        await asyncio.sleep(1)
        
        # Run client test
        await test_websocket_connection()
        
    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_websocket_communication()) 