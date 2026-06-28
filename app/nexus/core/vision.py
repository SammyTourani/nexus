"""
Local vision inference via Qwen3-VL-8B through Ollama.
Only called when the AX tree returns no interactive elements (Qt apps, web canvases).
Implements set-of-marks prompting for reliable element grounding.
"""
from __future__ import annotations

import base64
import io
import logging
import os
from dataclasses import dataclass
from typing import Optional

import mss
import mss.tools
import ollama
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen3-vl:8b")

# Grid overlay: divide screen into a grid and number each cell
# to give the model stable coordinate reference points
GRID_COLS = 20
GRID_ROWS = 15


@dataclass
class VisionResult:
    x: float
    y: float
    confidence: str
    raw_response: str


def _capture_screen() -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def _encode_image(img: Image.Image) -> str:
    """Encode PIL image to base64 for Ollama API."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _draw_set_of_marks(img: Image.Image) -> tuple[Image.Image, dict[int, tuple[float, float]]]:
    """
    Overlay numbered markers at regular grid positions.
    Returns the annotated image and a map from marker number to (x, y) coordinates.
    """
    annotated = img.copy()
    draw = ImageDraw.Draw(annotated)
    w, h = img.size

    cell_w = w / GRID_COLS
    cell_h = h / GRID_ROWS
    markers: dict[int, tuple[float, float]] = {}
    n = 1

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = col * cell_w + cell_w / 2
            cy = row * cell_h + cell_h / 2
            markers[n] = (cx, cy)

            # Draw small numbered circle
            r = 8
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 80, 0), outline=(255, 255, 255))
            label = str(n)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 8)
            except Exception:
                font = ImageFont.load_default()
            tw = draw.textlength(label, font=font)
            draw.text((cx - tw / 2, cy - 5), label, fill=(255, 255, 255), font=font)
            n += 1

    return annotated, markers


def _parse_marker_number(response: str) -> Optional[int]:
    """Extract the first integer from the model's response."""
    import re
    numbers = re.findall(r"\b(\d+)\b", response)
    for n in numbers:
        parsed = int(n)
        if 1 <= parsed <= GRID_COLS * GRID_ROWS:
            return parsed
    return None


class VisionEngine:
    """
    Qwen3-VL-8B via Ollama for element grounding.
    Uses set-of-marks: overlays numbered grid on screenshot, asks model which number
    is closest to the target element.
    """

    def __init__(self) -> None:
        self._client = ollama.Client(host=OLLAMA_HOST)
        self._verify_model()

    def _verify_model(self) -> None:
        try:
            models = self._client.list()
            names = [m.model for m in models.models]
            if not any(VISION_MODEL in name for name in names):
                log.warning(
                    "Vision model '%s' not found in Ollama. "
                    "Run: ollama pull %s",
                    VISION_MODEL,
                    VISION_MODEL,
                )
        except Exception as e:
            log.warning("Could not connect to Ollama at %s: %s", OLLAMA_HOST, e)

    def find_element(self, target_description: str, screenshot: Optional[Image.Image] = None) -> Optional[VisionResult]:
        """
        Find the screen coordinates of a UI element matching the description.
        Returns None if the model cannot locate the element with reasonable confidence.
        """
        img = screenshot or _capture_screen()
        annotated, markers = _draw_set_of_marks(img)
        w, h = img.size

        prompt = (
            f"The screenshot shows a macOS desktop with numbered markers overlaid in a grid.\n"
            f"Screen size: {w}x{h} pixels.\n\n"
            f"Task: Find the UI element that best matches this description: '{target_description}'\n\n"
            f"Instructions:\n"
            f"1. Look at the screenshot carefully\n"
            f"2. Find the element matching the description\n"
            f"3. Reply with ONLY the number of the marker closest to that element\n"
            f"4. If you cannot find it, reply with: NOT_FOUND\n\n"
            f"Your reply (a single number or NOT_FOUND):"
        )

        try:
            response = self._client.chat(
                model=VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [_encode_image(annotated)],
                }],
                options={"temperature": 0.0, "num_predict": 20},
            )
            raw = response.message.content.strip()
            log.debug("Vision response for '%s': %s", target_description, raw)

            if "NOT_FOUND" in raw.upper():
                return None

            marker_n = _parse_marker_number(raw)
            if marker_n and marker_n in markers:
                x, y = markers[marker_n]
                return VisionResult(x=x, y=y, confidence="medium", raw_response=raw)

            return None

        except Exception as e:
            log.error("Vision inference failed: %s", e)
            return None

    def describe_screen(self, screenshot: Optional[Image.Image] = None) -> str:
        """Return a plain-text description of the current screen state for the planner."""
        img = screenshot or _capture_screen()
        w, h = img.size

        prompt = (
            f"Describe the current macOS desktop screenshot in 2-3 sentences. "
            f"Focus on: what application is in the foreground, what content is visible, "
            f"and what interactive elements (buttons, text fields, menus) are present. "
            f"Be specific and brief."
        )

        try:
            response = self._client.chat(
                model=VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [_encode_image(img)],
                }],
                options={"temperature": 0.1, "num_predict": 150},
            )
            return response.message.content.strip()
        except Exception as e:
            log.error("Screen description failed: %s", e)
            return "Unable to describe screen."
