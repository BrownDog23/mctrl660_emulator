# fader_state.py
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class FaderSnapshot:
    left_value: int
    right_value: int
    last_update_monotonic: float
    last_peer: Optional[Tuple[str, int]] = None


class FaderState:
    """
    Thread-safe state store for LEFT/RIGHT fader values decoded from FE frames.
    Values are expected to be 0..255 (or 0..65535 depending on your decode),
    but we do not enforce range strictly here beyond int conversion.
    """

    def __init__(self, left_default: int = 0, right_default: int = 0):
        self._lock = threading.Lock()
        self._left = int(left_default)
        self._right = int(right_default)
        self._last_update = 0.0
        self._last_peer: Optional[Tuple[str, int]] = None

    def update_left(self, value: int, peer: Optional[Tuple[str, int]] = None) -> None:
        with self._lock:
            self._left = int(value)
            self._last_update = time.monotonic()
            self._last_peer = peer

    def update_right(self, value: int, peer: Optional[Tuple[str, int]] = None) -> None:
        with self._lock:
            self._right = int(value)
            self._last_update = time.monotonic()
            self._last_peer = peer

    def update(self, side: str, value: int, peer: Optional[Tuple[str, int]] = None) -> None:
        """
        side: "LEFT" or "RIGHT"
        """
        side_u = side.upper()
        if side_u == "LEFT":
            self.update_left(value, peer=peer)
        elif side_u == "RIGHT":
            self.update_right(value, peer=peer)
        else:
            # Unknown side: ignore but still record last update? No.
            return

    def snapshot(self) -> FaderSnapshot:
        with self._lock:
            return FaderSnapshot(
                left_value=self._left,
                right_value=self._right,
                last_update_monotonic=self._last_update,
                last_peer=self._last_peer,
            )

    def get_values(self) -> Tuple[int, int]:
        with self._lock:
            return self._left, self._right

    def get_last_update(self) -> float:
        with self._lock:
            return self._last_update
