from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

import cv2
import numpy as np

from prom_recognition.config import load_config
from prom_recognition.config import RoiConfig
from prom_recognition.debug_view import draw_detections
from prom_recognition.detector import CircleDetector
from prom_recognition.tracker import CircleTracker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract HPMA video frames and run circle detection.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--video", required=True)
    parser.add_argument("--project-video", default="data/videos/hpma.mp4")
    parser.add_argument("--frames-dir", default="data/screenshots/hpma_frames")
    parser.add_argument("--csv", default="data/annotations/hpma_detections.csv")
    parser.add_argument("--tracks-csv", default="data/annotations/hpma_tracks.csv")
    parser.add_argument("--debug-dir", default="data/annotations/hpma_debug")
    parser.add_argument("--samples-per-second", type=float, default=2.0)
    parser.add_argument("--dense-start-seconds", type=float, default=0.0)
    parser.add_argument("--dense-until-seconds", type=float, default=10.0)
    parser.add_argument("--dense-step-frames", type=int, default=10)
    parser.add_argument("--max-debug-frames", type=int, default=80)
    return parser.parse_args()


def copy_video(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def extract_frames(
    video_path: Path,
    frames_dir: Path,
    samples_per_second: float,
    dense_start: float,
    dense_until: float,
    dense_step: int,
) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise SystemExit(f"Could not read video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 60.0
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_step = max(1, int(round(fps / samples_per_second)))
    dense_start_frame = max(0, min(total, int(round(fps * dense_start))))
    dense_until_frame = max(dense_start_frame, min(total, int(round(fps * dense_until))))
    frame_indices = set(range(0, total, sample_step)) | set(
        range(dense_start_frame, dense_until_frame, dense_step)
    )

    saved = 0
    for frame_index in sorted(frame_indices):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            continue
        timestamp = frame_index / fps
        output = frames_dir / f"hpma_f{frame_index:06d}_t{timestamp:07.3f}.png"
        cv2.imwrite(str(output), frame)
        saved += 1

    capture.release()
    return saved


def crop_frame(frame: np.ndarray, crop: RoiConfig | None) -> np.ndarray:
    if crop is None:
        return frame
    return frame[crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]


def analyze_frames(
    config_path: Path,
    frames_dir: Path,
    csv_path: Path,
    tracks_csv_path: Path,
    debug_dir: Path,
    max_debug_frames: int,
) -> tuple[int, int]:
    config = load_config(config_path)
    detector = CircleDetector(config.detector)
    tracker = CircleTracker(config.tracker.max_center_distance, config.tracker.max_missing_frames)
    all_tracks = {}
    debug_dir.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[list[object]] = []
    debug_saved = 0
    pattern = re.compile(r"_f(\d+)_t([0-9.]+)\.png$")

    for frame_path in sorted(frames_dir.glob("*.png")):
        frame = cv2.imread(str(frame_path))
        if frame is None:
            continue
        frame = crop_frame(frame, config.video.input_crop)

        match = pattern.search(frame_path.name)
        frame_index = int(match.group(1)) if match else -1
        timestamp = float(match.group(2)) if match else 0.0

        detections = detector.detect(frame, config.roi)
        active_tracks = tracker.update(timestamp, detections)
        for track in active_tracks:
            all_tracks[track.id] = track
        for detection_index, detection in enumerate(detections):
            rows.append(
                [
                    frame_index,
                    timestamp,
                    detection_index,
                    round(detection.x, 2),
                    round(detection.y, 2),
                    round(detection.radius, 2),
                    round(detection.confidence, 4),
                ]
            )

        if detections and debug_saved < max_debug_frames:
            cv2.imwrite(str(debug_dir / frame_path.name), draw_detections(frame, detections))
            debug_saved += 1

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["frame", "time_s", "detection_index", "x", "y", "radius", "confidence"])
        writer.writerows(rows)

    track_rows: list[list[object]] = []
    for track in all_tracks.values():
        if len(track.detections) < config.tracker.confirm_frames:
            continue
        first_time, first_detection = track.detections[0]
        last_time, last_detection = track.detections[-1]
        shrink_speed = track.shrink_speed()
        if shrink_speed is None or shrink_speed < config.tracker.min_shrink_speed:
            continue
        track_rows.append(
            [
                track.id,
                len(track.detections),
                round(first_time, 3),
                round(last_time, 3),
                round(last_time - first_time, 3),
                round(last_detection.x, 2),
                round(last_detection.y, 2),
                round(first_detection.radius, 2),
                round(last_detection.radius, 2),
                round(shrink_speed, 2),
            ]
        )

    with tracks_csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "track_id",
                "observations",
                "first_time_s",
                "last_time_s",
                "duration_s",
                "latest_x",
                "latest_y",
                "first_radius",
                "last_radius",
                "shrink_speed_px_s",
            ]
        )
        writer.writerows(track_rows)

    return len(rows), len(track_rows)


def main() -> None:
    args = parse_args()
    source_video = Path(args.video)
    project_video = copy_video(source_video, Path(args.project_video))
    saved_frames = extract_frames(
        project_video,
        Path(args.frames_dir),
        args.samples_per_second,
        args.dense_start_seconds,
        args.dense_until_seconds,
        args.dense_step_frames,
    )
    detections, tracks = analyze_frames(
        Path(args.config),
        Path(args.frames_dir),
        Path(args.csv),
        Path(args.tracks_csv),
        Path(args.debug_dir),
        args.max_debug_frames,
    )
    print(f"video={project_video}")
    print(f"frames_saved={saved_frames}")
    print(f"detections={detections}")
    print(f"shrinking_tracks={tracks}")
    print(f"csv={args.csv}")
    print(f"tracks_csv={args.tracks_csv}")
    print(f"debug_dir={args.debug_dir}")


if __name__ == "__main__":
    main()
