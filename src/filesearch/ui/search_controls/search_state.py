"""Search state enumeration."""

from enum import Enum


class SearchState(Enum):
    """Enumeration of possible search control states."""

    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"
