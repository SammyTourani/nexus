"""
Screenshot capture utilities shared across the vision and verifier modules.
Separates capture concerns from inference/verification concerns.
"""
from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Optional

import mss
import mss.tools
from PIL import Image


@dataclass
class Screenshot:
    image: Image.Image
    width: int
    height: int
    monitor_index: int

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def to_base64_png(self) -> str:
        buf = io.BytesIO()
        self.image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def to_base64_jpeg(self, quality: int = 85) -> str:
        buf = io.BytesIO()
        self.image.convert("RGB").save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode()

    def crop(self, x: int, y: int, w: int, h: int) -> "Screenshot":
        cropped = self.image.crop((x, y, x + w, y + h))
        return Screenshot(image=cropped, width=w, height=h, monitor_index=self.monitor_index)

    def is_blank(self, threshold: int = 5) -> bool:
        """
        Returns True when every sampled pixel is near-black.
        Used to detect failed Screen Recording permission (macOS returns black frames).
        """
        pixels = self.image.tobytes()
        sample_step = max(1, len(pixels) // 1000)
        return all(b <= threshold for b in pixels[::sample_step])


def capture(monitor: int = 1) -> Screenshot:
    """Capture the primary (or specified) monitor."""
    with mss.mss() as sct:
        mon = sct.monitors[monitor]
        raw = sct.grab(mon)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        return Screenshot(
            image=img,
            width=raw.width,
            height=raw.height,
            monitor_index=monitor,
        )


def capture_all_monitors() -> list[Screenshot]:
    """Capture every connected display."""
    with mss.mss() as sct:
        screenshots = []
        for i, mon in enumerate(sct.monitors[1:], start=1):
            raw = sct.grab(mon)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            screenshots.append(Screenshot(image=img, width=raw.width, height=raw.height, monitor_index=i))
        return screenshots
