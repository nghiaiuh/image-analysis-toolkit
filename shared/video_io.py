from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class VideoInfo:
    path: str
    frame_count: int
    fps: float
    width: int
    height: int
    duration_seconds: float


def get_video_metadata(path: str | Path) -> VideoInfo:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {path}")
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        capture.release()
    return VideoInfo(
        path=str(path),
        frame_count=max(frame_count, 1),
        fps=fps,
        width=width,
        height=height,
        duration_seconds=(frame_count / fps) if fps else 0.0,
    )


def extract_video_frame(path: str | Path, frame_index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {path}")
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index))
        success, frame = capture.read()
    finally:
        capture.release()
    if not success or frame is None:
        raise ValueError(f"Unable to read frame {frame_index} from video: {path}")
    return frame


def load_first_video_frame(path: str | Path) -> np.ndarray:
    return extract_video_frame(path, 0)
