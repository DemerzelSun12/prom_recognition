from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass

import cv2
import mss
import numpy as np


@dataclass(frozen=True)
class WindowRegion:
    left: int
    top: int
    width: int
    height: int


def enable_dpi_awareness() -> None:
    if platform.system() != "Windows":
        return

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class ScreenCapture:
    def __init__(self) -> None:
        self._screen_capture = mss.mss()

    def grab_window(self, region: WindowRegion) -> np.ndarray:
        monitor = {
            "left": region.left,
            "top": region.top,
            "width": region.width,
            "height": region.height,
        }
        frame = np.asarray(self._screen_capture.grab(monitor))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def close(self) -> None:
        self._screen_capture.close()

    def __enter__(self) -> ScreenCapture:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
