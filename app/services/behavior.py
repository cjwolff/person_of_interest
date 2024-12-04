import numpy as np
from typing import List, Dict
from ..schemas.analysis import (
    BehaviorAnalysis,
    PoseData,
    RiskLevel,
    DetectedBehavior
)

class BehaviorAnalysisService:
    def __init__(self):
        self.pose_history: Dict[str, List[PoseData]] = {}
        self.history_length = 30
        
    def analyze_pose(self, pose_data: PoseData) -> BehaviorAnalysis:
        user_id = pose_data.user_id
        if user_id not in self.pose_history:
            self.pose_history[user_id] = []
            
        history = self.pose_history[user_id]
        history.append(pose_data)
        if len(history) > self.history_length:
            history.pop(0)
            
        behaviors = []
        risk_score = 0
        
        # Check for erratic movement
        if self._has_erratic_movement(history):
            behaviors.append(DetectedBehavior.ERRATIC_MOVEMENT)
            risk_score += 2
            
        # Check for unstable posture
        if self._has_unstable_posture(history):
            behaviors.append(DetectedBehavior.UNSTABLE_POSTURE)
            risk_score += 2
            
        # Check for aggressive gestures
        if self._has_aggressive_gestures(history):
            behaviors.append(DetectedBehavior.AGGRESSIVE_GESTURES)
            risk_score += 3
            
        # Check for loitering
        if self._is_loitering(history):
            behaviors.append(DetectedBehavior.LOITERING)
            risk_score += 1
            
        return BehaviorAnalysis(
            timestamp=pose_data.timestamp,
            risk_level=self._calculate_risk_level(risk_score),
            behaviors=behaviors,
            confidence=self._calculate_confidence(history)
        )
        
    def _has_erratic_movement(self, history: List[PoseData]) -> bool:
        if len(history) < 3:
            return False
            
        velocities = []
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            dt = (curr.timestamp - prev.timestamp).total_seconds()
            if dt > 0:
                velocity = np.linalg.norm(
                    np.array([curr.x - prev.x, curr.y - prev.y]) / dt
                )
                velocities.append(velocity)
                
        if not velocities:
            return False
            
        velocity_std = np.std(velocities)
        return velocity_std > 2.0  # Threshold for erratic movement
        
    def _has_unstable_posture(self, history: List[PoseData]) -> bool:
        if len(history) < 5:
            return False
            
        head_angles = [pose.head_angle for pose in history if pose.head_angle]
        if not head_angles:
            return False
            
        angle_std = np.std(head_angles)
        return angle_std > 15.0  # Threshold for unstable posture
        
    def _has_aggressive_gestures(self, history: List[PoseData]) -> bool:
        if len(history) < 3:
            return False
            
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            dt = (curr.timestamp - prev.timestamp).total_seconds()
            if dt > 0:
                # Calculate acceleration of key points
                for landmark in ["leftWrist", "rightWrist", "leftElbow", "rightElbow"]:
                    if landmark in curr.landmarks and landmark in prev.landmarks:
                        acceleration = np.linalg.norm(
                            np.array([
                                curr.landmarks[landmark].x - prev.landmarks[landmark].x,
                                curr.landmarks[landmark].y - prev.landmarks[landmark].y
                            ]) / (dt * dt)
                        )
                        if acceleration > 5.0:  # Threshold for aggressive movement
                            return True
        return False
        
    def _is_loitering(self, history: List[PoseData]) -> bool:
        if len(history) < 10:
            return False
            
        total_time = (history[-1].timestamp - history[0].timestamp).total_seconds()
        if total_time < 300:  # Less than 5 minutes
            return False
            
        # Calculate total distance moved
        total_distance = 0
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            distance = np.linalg.norm(
                np.array([curr.x - prev.x, curr.y - prev.y])
            )
            total_distance += distance
            
        return total_distance < 10.0  # Less than 10 meters total movement
        
    def _calculate_risk_level(self, risk_score: int) -> RiskLevel:
        if risk_score >= 6:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
        
    def _calculate_confidence(self, history: List[PoseData]) -> float:
        if not history:
            return 0.0
        return sum(pose.confidence for pose in history) / len(history)