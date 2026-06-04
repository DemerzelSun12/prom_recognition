from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from prom_recognition.config import DetectorConfig, RoiConfig


@dataclass(frozen=True)
class CircleDetection:
    x: float
    y: float
    radius: float
    confidence: float = 1.0


class CircleDetector:
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config

    def detect(self, frame: np.ndarray, roi: RoiConfig) -> list[CircleDetection]:
        roi_frame = frame[roi.y : roi.y + roi.height, roi.x : roi.x + roi.width]
        hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(self.config.hsv_lower), np.array(self.config.hsv_upper))

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        edges = cv2.Canny(mask, self.config.canny_threshold1, self.config.canny_threshold2)
        circles = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=self.config.hough_dp,
            minDist=self.config.hough_min_dist,
            param1=self.config.hough_param1,
            param2=self.config.hough_param2,
            minRadius=self.config.min_radius,
            maxRadius=self.config.max_radius,
        )

        if circles is None:
            return []

        detections: list[CircleDetection] = []
        for x, y, radius in np.round(circles[0, :]).astype(float):
            detections.append(CircleDetection(x=x + roi.x, y=y + roi.y, radius=radius))
        return detections

