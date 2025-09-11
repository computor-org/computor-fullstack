from enum import Enum

class TaskStatus(str, Enum):
    """Task execution status enumeration."""
    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"

def map_task_status_to_int(status: TaskStatus) -> int:
    """Map TaskStatus enum to legacy integer for database storage."""
    mapping = {
        TaskStatus.FINISHED: 0,    # FINISHED -> COMPLETED (0)
        TaskStatus.FAILED: 1,      # FAILED -> FAILED (1)
        TaskStatus.CANCELLED: 2,   # CANCELLED -> CANCELLED (2)
        TaskStatus.QUEUED: 4,      # QUEUED -> PENDING (4)
        TaskStatus.STARTED: 5,     # STARTED -> RUNNING (5)
        TaskStatus.DEFERRED: 7     # DEFERRED -> PAUSED (7)
    }
    return mapping.get(status, 1)  # Default to FAILED (1)