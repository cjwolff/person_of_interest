from fastapi import FastAPI, HTTPException, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import numpy as np
import cv2
import base64
from typing import List, Dict, Optional
from datetime import datetime
import logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import warnings
import os

# Import services
from app.services.tracking_service import TrackingService
from app.services.face_detection_service import FaceDetectionService
from app.services.object_detection_service import ObjectDetectionService
from app.services.ar_service import ARService
from app.services.behavior_analysis_service import BehaviorAnalysisService
from app.services.geofencing_service import GeofencingService
from app.services.video_processor import VideoProcessor
from app.ml_engine import MLEngine

# Import core components
from app.core.websocket import WebSocketManager
from app.core.auth import WebSocketAuthManager

# Set up logging
logger = logging.getLogger(__name__)

# Import models
from app.models.detection import Detection, FaceLandmarks, DetectionResponse
from app.models.frame import FrameRequest

# Import routes
from app.api.routes import auth
from app.api.websocket_handler import SurveillanceWebSocketHandler
from app.api.websocket_routes import router as websocket_router

app = FastAPI(title="Person of Interest API")

# Initialize managers
ws_manager = WebSocketManager()
auth_manager = WebSocketAuthManager()

# Initialize services
face_detector = FaceDetectionService()
object_detector = ObjectDetectionService()
tracker = TrackingService()
ar_service = ARService(object_detector=object_detector, face_detector=face_detector)
behavior_analyzer = BehaviorAnalysisService()
geofencing = GeofencingService()
video_processor = VideoProcessor()

# Initialize ML engine with services
ml_engine = MLEngine(
    face_detector=face_detector,
    object_detector=object_detector,
    tracker=tracker,
    ar_service=ar_service,
    behavior_analyzer=behavior_analyzer
)

# Initialize WebSocket handler
ws_handler = SurveillanceWebSocketHandler(
    websocket_manager=ws_manager,
    video_processor=video_processor,
    ar_service=ar_service,
    behavior_service=behavior_analyzer,
    geofencing_service=geofencing
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(
    websocket_router,
    prefix="/ws",
    tags=["websocket"]
)

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

async def process_frame(image: np.ndarray) -> DetectionResponse:
    """Process a frame using the initialized services"""
    try:
        # Detect faces and objects
        faces = await face_detector.detect_faces(image)
        objects = await object_detector.detect(image)
        
        # Update tracking with frame
        tracked_objects = await tracker.update(objects, frame=image)
        
        # Get AR data
        ar_data = await ar_service.process_frame(image, faces, tracked_objects)
        
        # Analyze behavior
        behavior_data = await behavior_analyzer.analyze(tracked_objects)
        
        # Check geofencing
        geofencing_alerts = await geofencing.check(tracked_objects)
        
        return DetectionResponse(
            faces=faces,
            objects=tracked_objects,
            ar_data=ar_data,
            behavior_analysis=behavior_data,
            geofencing_alerts=geofencing_alerts
        )
        
    except Exception as e:
        logger.error(f"Error in process_frame: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Frame processing error", "message": str(e)}
        )

@app.post("/api/detect")
async def detect_frame(request: FrameRequest):
    try:
        logger.debug(f"Received frame. Size: {request.width}x{request.height}")
        logger.debug(f"Metadata: {request.metadata}")
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("Failed to decode image data")
                raise HTTPException(status_code=400, detail="Invalid image data")
                
            # Log successful decode
            logger.debug(f"Successfully decoded image. Shape: {img.shape}")
            
            # Process frame
            results = await process_frame(img)
            return results
            
        except Exception as decode_error:
            logger.error(f"Image decoding error: {decode_error}")
            raise HTTPException(
                status_code=400, 
                detail={"error": "Image decoding error", "message": str(decode_error)}
            )
            
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(
            status_code=400,
            detail={"error": "Validation error", "message": str(ve)}
        )
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Processing error", "message": str(e)}
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    import uvicorn
    # Suppress warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    uvicorn.run(app, host="0.0.0.0", port=8000)