"""In-memory metrics for job lifecycle tracking."""

import threading


class Metrics:
    """Thread-safe in-memory metrics counters."""

    def __init__(self):
        self._lock = threading.Lock()
        self.jobs_created = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self._processing_times: list[float] = []

    def record_job_created(self) -> None:
        with self._lock:
            self.jobs_created += 1

    def record_job_completed(self, processing_time: float | None = None) -> None:
        with self._lock:
            self.jobs_completed += 1
            if processing_time is not None:
                self._processing_times.append(processing_time)

    def record_job_failed(self) -> None:
        with self._lock:
            self.jobs_failed += 1

    @property
    def avg_processing_time(self) -> float:
        with self._lock:
            if not self._processing_times:
                return 0.0
            return sum(self._processing_times) / len(self._processing_times)

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "jobs_created": self.jobs_created,
                "jobs_completed": self.jobs_completed,
                "jobs_failed": self.jobs_failed,
                "avg_processing_time_seconds": round(
                    sum(self._processing_times) / len(self._processing_times)
                    if self._processing_times
                    else 0.0,
                    2,
                ),
            }


# Singleton instance
metrics = Metrics()
