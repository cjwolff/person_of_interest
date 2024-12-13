import logging
from datetime import datetime
from typing import List
from app.services.face_detection_service import FaceDetectionService
from app.services.object_detection_service import ObjectDetectionService
from app.services.tracking_service import TrackingService
from app.services.ar_service import ARService
from app.services.behavior_analysis_service import BehaviorAnalysisService

logger = logging.getLogger(__name__)

class MLEngine:
    def __init__(
        self,
        face_detector: FaceDetectionService,
        object_detector: ObjectDetectionService,
        tracker: TrackingService,
        ar_service: ARService,
        behavior_analyzer: BehaviorAnalysisService
    ):
        self.face_detector = face_detector
        self.object_detector = object_detector
        self.tracker = tracker
        self.ar_service = ar_service
        self.behavior_analyzer = behavior_analyzer
        
        logger.info("ML Engine initialized with all services")

    async def process_frame(self, frame):
        """Process a single frame through all ML services"""
        try:
            # Detect faces and objects
            faces = await self.face_detector.detect_faces(frame)
            objects = await self.object_detector.detect(frame)
            
            # Update tracking
            tracked_objects = await self.tracker.update(objects, frame=frame)
            
            # Get AR overlays
            ar_data = await self.ar_service.process_frame(frame, faces, tracked_objects)
            
            # Analyze behavior
            behavior_data = await self.behavior_analyzer.analyze(tracked_objects)
            
            return {
                "faces": faces,
                "objects": tracked_objects,
                "ar_data": ar_data,
                "behavior_analysis": behavior_data
            }
            
        except Exception as e:
            logger.error(f"Error in ML Engine frame processing: {e}")
            raise
