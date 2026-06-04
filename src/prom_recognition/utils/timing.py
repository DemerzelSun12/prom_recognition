from __future__ import annotations


def predict_trigger_time(
    now: float,
    current_radius: float,
    target_radius: float,
    shrink_speed: float,
    click_offset_ms: int,
) -> float | None:
    if shrink_speed <= 0 or current_radius <= target_radius:
        return None
    seconds_until_target = (current_radius - target_radius) / shrink_speed
    return now + seconds_until_target - click_offset_ms / 1000.0

