from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from prom_recognition.config import load_config
from prom_recognition.debug_view import draw_detections
from prom_recognition.detector import CircleDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect prom rhythm circles from an image.")
    parser.add_argument("--config", default="configs/default.yaml", help="Path to YAML config.")
    parser.add_argument("--image", help="Path to a test image.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    if not args.image:
        raise SystemExit("Please provide --image for the first milestone.")

    image_path = Path(args.image)
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise SystemExit(f"Could not read image: {image_path}")

    detector = CircleDetector(config.detector)
    detections = detector.detect(frame, config.roi)
    debug_frame = draw_detections(frame, detections)

    cv2.imshow("prom recognition debug", debug_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

