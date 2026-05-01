import { useState, useCallback } from "react";
import { JobForm } from "../components/JobForm";
import { JobList } from "../components/JobList";
import { Toast } from "../components/Toast";
import { Layout } from "../components/Layout";
import { useJobs } from "../hooks/useJobs";

interface DashboardPageProps {
  onLogout: () => void;
  username: string;
}

export function DashboardPage({ onLogout, username }: DashboardPageProps) {
  const { jobs, loading, refresh } = useJobs();
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const handleSuccess = useCallback((message: string) => {
    setToast({ message, type: "success" });
  }, []);

  const handleError = useCallback((message: string) => {
    setToast({ message, type: "error" });
  }, []);

  return (
    <Layout onLogout={onLogout} username={username}>
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
      <JobForm onJobCreated={refresh} onError={handleError} onSuccess={handleSuccess} />
      <JobList jobs={jobs} loading={loading} />
    </Layout>
  );
}
