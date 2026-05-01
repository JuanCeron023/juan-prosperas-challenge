import { useState, useEffect, useCallback, useRef } from "react";
import { apiRequest } from "../api/client";
import { Job, JobListResponse, JobStatus } from "../types";
import { useSSE } from "./useSSE";

export function useJobs(pollingInterval: number = 5000) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await apiRequest<JobListResponse>("/jobs");
      setJobs(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch jobs");
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchJobs();
    setLoading(false);
  }, [fetchJobs]);

  // SSE handler: update a single job's status in-place
  const handleJobUpdate = useCallback(
    (jobId: string, status: string, updatedAt: string, resultUrl?: string | null) => {
      setJobs((prevJobs) =>
        prevJobs.map((job) =>
          job.job_id === jobId
            ? {
                ...job,
                status: status as JobStatus,
                updated_at: updatedAt,
                ...(resultUrl !== undefined && { result_url: resultUrl }),
              }
            : job
        )
      );
    },
    []
  );

  // Use SSE for real-time updates
  const { connected, usingFallback } = useSSE({
    onJobUpdate: handleJobUpdate,
  });

  // Initial fetch
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Polling fallback: only poll when SSE is not connected or using fallback
  useEffect(() => {
    if (connected && !usingFallback) {
      // SSE is active, no need for polling
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Fall back to polling
    intervalRef.current = window.setInterval(fetchJobs, pollingInterval);
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [fetchJobs, pollingInterval, connected, usingFallback]);

  return { jobs, total, loading, error, refresh };
}
