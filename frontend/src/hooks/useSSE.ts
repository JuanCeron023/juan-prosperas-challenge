import { useEffect, useRef, useState, useCallback } from "react";

interface SSEOptions {
  onJobUpdate: (jobId: string, status: string, updatedAt: string, resultUrl?: string | null) => void;
  reconnectTimeout?: number;
}

export function useSSE(options: SSEOptions) {
  const {
    onJobUpdate,
    reconnectTimeout = 30000,
  } = options;
  const [connected, setConnected] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    // EventSource doesn't support custom headers, so pass token as query param
    const es = new EventSource(`/stream/jobs?token=${token}`);

    es.onopen = () => {
      setConnected(true);
      setUsingFallback(false);
      // Clear any pending fallback timer on successful connection
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onJobUpdate(data.job_id, data.status, data.updated_at, data.result_url);
      } catch {
        // Ignore parse errors (heartbeats, etc.)
      }
    };

    es.onerror = () => {
      es.close();
      setConnected(false);

      // Set a timer to fall back to polling if reconnection fails
      if (!reconnectTimerRef.current) {
        reconnectTimerRef.current = window.setTimeout(() => {
          setUsingFallback(true);
          reconnectTimerRef.current = null;
        }, reconnectTimeout);
      }

      // Try reconnecting after a short delay
      reconnectAttemptRef.current = window.setTimeout(connect, 3000);
    };

    eventSourceRef.current = es;
  }, [onJobUpdate, reconnectTimeout]);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      if (reconnectAttemptRef.current) {
        window.clearTimeout(reconnectAttemptRef.current);
      }
    };
  }, [connect]);

  return { connected, usingFallback };
}
