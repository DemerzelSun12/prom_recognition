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
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.config.hsv_ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(lower), np.array(upper)))

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.medianBlur(mask, 5)

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
            confidence = self._ring_score(mask, int(x), int(y), int(radius))
            if confidence < self.config.min_ring_score:
                continue
            detections.append(
                CircleDetection(x=x + roi.x, y=y + roi.y, radius=radius, confidence=confidence)
            )
        return self._deduplicate(detections)[: self.config.max_detections]

    @staticmethod
    def _ring_score(mask: np.ndarray, x: int, y: int, radius: int) -> float:
        if radius <= 0:
            return 0.0
        sample_count = max(48, int(2 * np.pi * radius / 3))
        angles = np.linspace(0, 2 * np.pi, sample_count, endpoint=False)
        xs = np.round(x + np.cos(angles) * radius).astype(int)
        ys = np.round(y + np.sin(angles) * radius).astype(int)
        inside = (xs >= 0) & (xs < mask.shape[1]) & (ys >= 0) & (ys < mask.shape[0])
        if not np.any(inside):
            return 0.0
        return float(np.count_nonzero(mask[ys[inside], xs[inside]]) / np.count_nonzero(inside))

    @staticmethod
    def _deduplicate(detections: list[CircleDetection]) -> list[CircleDetection]:
        ordered = sorted(detections, key=lambda item: item.confidence, reverse=True)
        kept: list[CircleDetection] = []
        for detection in ordered:
            overlaps = False
            for existing in kept:
                center_distance = np.hypot(detection.x - existing.x, detection.y - existing.y)
                radius_distance = abs(detection.radius - existing.radius)
                if center_distance < 40 and radius_distance < 30:
                    overlaps = True
                    break
            if not overlaps:
                kept.append(detection)
        return kept

