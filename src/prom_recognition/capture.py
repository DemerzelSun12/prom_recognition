from __future__ import annotations

import ctypes
from dataclasses import dataclass


@dataclass(frozen=True)
class WindowRegion:
    left: int
    top: int
    width: int
    height: int


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class ScreenCapture:
    def grab_window(self, region: WindowRegion):
        raise NotImplementedError("Implement with mss or dxcam on Windows.")

