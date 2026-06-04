from __future__ import annotations

import cv2
import numpy as np

from prom_recognition.detector import CircleDetection


def draw_detections(frame: np.ndarray, detections: list[CircleDetection]) -> np.ndarray:
    output = frame.copy()
    for detection in detections:
        center = (int(detection.x), int(detection.y))
        radius = int(detection.radius)
        cv2.circle(output, center, radius, (0, 255, 0), 2)
        cv2.circle(output, center, 3, (0, 0, 255), -1)
        cv2.putText(
            output,
            f"r={radius} c={detection.confidence:.2f}",
            (center[0] + 8, center[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    return output

