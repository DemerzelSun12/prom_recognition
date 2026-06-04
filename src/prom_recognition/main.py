from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from prom_recognition.config import load_config
from prom_recognition.config import RoiConfig
from prom_recognition.debug_view import draw_detections
from prom_recognition.detector import CircleDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect prom rhythm circles from an image or video.")
    parser.add_argument("--config", default="configs/default.yaml", help="Path to YAML config.")
    parser.add_argument("--image", help="Path to a test image.")
    parser.add_argument("--video", help="Path to a test video.")
    return parser.parse_args()


def crop_frame(frame: np.ndarray, crop: RoiConfig | None) -> np.ndarray:
    if crop is None:
        return frame
    return frame[crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]


def detect_and_show(frame: np.ndarray, detector: CircleDetector, roi: RoiConfig, delay_ms: int) -> bool:
    detections = detector.detect(frame, roi)
    debug_frame = draw_detections(frame, detections)
    cv2.imshow("prom recognition debug", debug_frame)
    key = cv2.waitKey(delay_ms) & 0xFF
    return key not in (ord("q"), 27)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    if bool(args.image) == bool(args.video):
        raise SystemExit("Please provide exactly one of --image or --video.")

    detector = CircleDetector(config.detector)

    if args.image:
        image_path = Path(args.image)
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise SystemExit(f"Could not read image: {image_path}")

        frame = crop_frame(frame, config.video.input_crop)
        detect_and_show(frame, detector, config.roi, 0)
    else:
        video_path = Path(args.video)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise SystemExit(f"Could not read video: {video_path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 30
        delay_ms = max(1, int(1000 / fps))
        frame_index = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % config.video.frame_step == 0:
                frame = crop_frame(frame, config.video.input_crop)
                if not detect_and_show(frame, detector, config.roi, delay_ms):
                    break
            frame_index += 1

        capture.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

