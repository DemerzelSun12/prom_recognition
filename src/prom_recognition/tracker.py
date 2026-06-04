from __future__ import annotations

from dataclasses import dataclass, field

from prom_recognition.detector import CircleDetection
from prom_recognition.utils.geometry import distance


@dataclass
class CircleTrack:
    id: int
    detections: list[tuple[float, CircleDetection]] = field(default_factory=list)
    missing_frames: int = 0
    clicked: bool = False

    @property
    def latest(self) -> CircleDetection:
        return self.detections[-1][1]

    def add(self, timestamp: float, detection: CircleDetection) -> None:
        self.detections.append((timestamp, detection))
        self.missing_frames = 0

    def shrink_speed(self) -> float | None:
        if len(self.detections) < 2:
            return None
        t0, first = self.detections[0]
        t1, last = self.detections[-1]
        elapsed = t1 - t0
        if elapsed <= 0:
            return None
        return (first.radius - last.radius) / elapsed


class CircleTracker:
    def __init__(self, max_center_distance: float, max_missing_frames: int) -> None:
        self.max_center_distance = max_center_distance
        self.max_missing_frames = max_missing_frames
        self._next_id = 1
        self.tracks: list[CircleTrack] = []

    def update(self, timestamp: float, detections: list[CircleDetection]) -> list[CircleTrack]:
        unmatched = detections[:]

        for track in self.tracks:
            match = self._find_match(track, unmatched)
            if match is None:
                track.missing_frames += 1
                continue
            track.add(timestamp, match)
            unmatched.remove(match)

        for detection in unmatched:
            track = CircleTrack(id=self._next_id)
            self._next_id += 1
            track.add(timestamp, detection)
            self.tracks.append(track)

        self.tracks = [track for track in self.tracks if track.missing_frames <= self.max_missing_frames]
        return self.tracks

    def _find_match(
        self,
        track: CircleTrack,
        detections: list[CircleDetection],
    ) -> CircleDetection | None:
        if not detections:
            return None
        candidates = sorted(
            detections,
            key=lambda detection: distance((track.latest.x, track.latest.y), (detection.x, detection.y)),
        )
        best = candidates[0]
        if distance((track.latest.x, track.latest.y), (best.x, best.y)) <= self.max_center_distance:
            return best
        return None

