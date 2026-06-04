from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import cv2
import numpy as np

from prom_recognition.config import RoiConfig
from prom_recognition.config import load_config


CSV_HEADER = ["image", "x", "y", "outer_radius", "color", "state", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manually annotate HPMA circle centers and radii.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--frames-dir", default="data/screenshots/hpma_frames")
    parser.add_argument("--output", default="data/annotations/hpma_manual_circles.csv")
    parser.add_argument("--start", default="")
    parser.add_argument("--scale", type=float, default=0.5)
    parser.add_argument("--color", default="unknown")
    parser.add_argument("--state", default="shrinking")
    return parser.parse_args()


def crop_frame(frame: np.ndarray, crop: RoiConfig | None) -> np.ndarray:
    if crop is None:
        return frame
    return frame[crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]


def ensure_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(CSV_HEADER)


def append_row(path: Path, row: list[object]) -> None:
    with path.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(row)


def read_csv_rows(path: Path) -> list[list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        rows = list(reader)
    return rows[1:] if rows and rows[0] == CSV_HEADER else rows


def write_csv_rows(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)


def draw_preview(
    frame: np.ndarray,
    image_name: str,
    index: int,
    total: int,
    saved: list[tuple[int, int, int]],
    center: tuple[int, int] | None,
    cursor: tuple[int, int] | None,
) -> np.ndarray:
    output = frame.copy()
    for x, y, radius in saved:
        cv2.circle(output, (x, y), radius, (0, 255, 0), 2)
        cv2.circle(output, (x, y), 4, (0, 0, 255), -1)
        cv2.putText(output, f"{x},{y} r={radius}", (x + 8, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    if center is not None:
        cv2.circle(output, center, 5, (0, 255, 255), -1)
        if cursor is not None:
            radius = round(math.hypot(cursor[0] - center[0], cursor[1] - center[1]))
            cv2.circle(output, center, radius, (0, 255, 255), 2)
            cv2.putText(
                output,
                f"preview r={radius}",
                (center[0] + 8, center[1] + 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

    help_text = f"{index + 1}/{total} {image_name} | left: center/edge  u: undo  n/p: next/prev  q: quit"
    cv2.rectangle(output, (0, 0), (output.shape[1], 38), (0, 0, 0), -1)
    cv2.putText(output, help_text, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    return output


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    frames = sorted(Path(args.frames_dir).glob("*.png"))
    if not frames:
        raise SystemExit(f"No PNG frames found in {args.frames_dir}")

    index = 0
    if args.start:
        for frame_index, frame_path in enumerate(frames):
            if frame_path.name == args.start:
                index = frame_index
                break

    output_csv = Path(args.output)
    ensure_csv(output_csv)
    csv_rows: list[list[object]] = read_csv_rows(output_csv)

    center: tuple[int, int] | None = None
    cursor: tuple[int, int] | None = None
    saved_for_image: dict[str, list[tuple[int, int, int]]] = {}
    window = "hpma circle annotator"

    def on_mouse(event: int, x: int, y: int, _flags: int, _param: object) -> None:
        nonlocal center, cursor
        raw_x = int(round(x / args.scale))
        raw_y = int(round(y / args.scale))
        cursor = (raw_x, raw_y)
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        image_name = frames[index].name
        if center is None:
            center = (raw_x, raw_y)
            return

        radius = round(math.hypot(raw_x - center[0], raw_y - center[1]))
        if radius <= 0:
            center = None
            return
        saved_for_image.setdefault(image_name, []).append((center[0], center[1], radius))
        csv_rows.append([image_name, center[0], center[1], radius, args.color, args.state, ""])
        write_csv_rows(output_csv, csv_rows)
        print(f"saved {image_name}: x={center[0]} y={center[1]} r={radius}")
        center = None

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        frame = cv2.imread(str(frames[index]))
        if frame is None:
            index = min(index + 1, len(frames) - 1)
            continue
        frame = crop_frame(frame, config.video.input_crop)
        preview = draw_preview(
            frame,
            frames[index].name,
            index,
            len(frames),
            saved_for_image.get(frames[index].name, []),
            center,
            cursor,
        )
        if args.scale != 1.0:
            preview = cv2.resize(preview, None, fx=args.scale, fy=args.scale, interpolation=cv2.INTER_AREA)

        cv2.imshow(window, preview)
        key = cv2.waitKey(30) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord("n"):
            center = None
            index = min(index + 1, len(frames) - 1)
        elif key == ord("p"):
            center = None
            index = max(index - 1, 0)
        elif key == ord("u"):
            image_name = frames[index].name
            if saved_for_image.get(image_name):
                removed = saved_for_image[image_name].pop()
                for row_index in range(len(csv_rows) - 1, -1, -1):
                    row = csv_rows[row_index]
                    if (
                        row[0] == image_name
                        and int(row[1]) == removed[0]
                        and int(row[2]) == removed[1]
                        and int(row[3]) == removed[2]
                    ):
                        csv_rows.pop(row_index)
                        write_csv_rows(output_csv, csv_rows)
                        break
                print(f"undo {image_name}: x={removed[0]} y={removed[1]} r={removed[2]}")
            else:
                center = None

    cv2.destroyAllWindows()
    print(f"annotations written to {output_csv}")


if __name__ == "__main__":
    main()
