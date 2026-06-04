from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RoiConfig:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class DetectorConfig:
    hsv_lower: tuple[int, int, int]
    hsv_upper: tuple[int, int, int]
    min_radius: int
    max_radius: int
    canny_threshold1: int
    canny_threshold2: int
    hough_dp: float
    hough_min_dist: int
    hough_param1: int
    hough_param2: int


@dataclass(frozen=True)
class TrackerConfig:
    max_center_distance: float
    confirm_frames: int
    max_missing_frames: int
    min_shrink_speed: float


@dataclass(frozen=True)
class TimingConfig:
    target_radius: float
    click_offset_ms: int


@dataclass(frozen=True)
class AppConfig:
    roi: RoiConfig
    detector: DetectorConfig
    tracker: TrackerConfig
    timing: TimingConfig


def load_config(path: str | Path) -> AppConfig:
    with Path(path).open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    return AppConfig(
        roi=RoiConfig(**raw["roi"]),
        detector=DetectorConfig(
            hsv_lower=tuple(raw["detector"]["hsv_lower"]),
            hsv_upper=tuple(raw["detector"]["hsv_upper"]),
            min_radius=raw["detector"]["min_radius"],
            max_radius=raw["detector"]["max_radius"],
            canny_threshold1=raw["detector"]["canny_threshold1"],
            canny_threshold2=raw["detector"]["canny_threshold2"],
            hough_dp=raw["detector"]["hough_dp"],
            hough_min_dist=raw["detector"]["hough_min_dist"],
            hough_param1=raw["detector"]["hough_param1"],
            hough_param2=raw["detector"]["hough_param2"],
        ),
        tracker=TrackerConfig(**raw["tracker"]),
        timing=TimingConfig(**raw["timing"]),
    )

