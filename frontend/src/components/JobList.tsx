import { Job } from "../types";
import { JobStatusBadge } from "./JobStatusBadge";

interface JobListProps {
  jobs: Job[];
  loading: boolean;
}

export function JobList({ jobs, loading }: JobListProps) {
  if (loading && jobs.length === 0) {
    return <p>Loading jobs...</p>;
  }

  if (jobs.length === 0) {
    return <p style={{ color: "#6c757d" }}>No reports yet. Create one above.</p>;
  }

  return (
    <div>
      <h3>Your Reports</h3>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #dee2e6", textAlign: "left" }}>
              <th style={{ padding: "8px" }}>Type</th>
              <th style={{ padding: "8px" }}>Format</th>
              <th style={{ padding: "8px" }}>Status</th>
              <th style={{ padding: "8px" }}>Created</th>
              <th style={{ padding: "8px" }}>Result</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.job_id} style={{ borderBottom: "1px solid #dee2e6" }}>
                <td style={{ padding: "8px", textTransform: "capitalize" }}>{job.report_type}</td>
                <td style={{ padding: "8px", textTransform: "uppercase" }}>{job.report_type}</td>
                <td style={{ padding: "8px" }}><JobStatusBadge status={job.status} /></td>
                <td style={{ padding: "8px" }}>{new Date(job.created_at).toLocaleString()}</td>
                <td style={{ padding: "8px" }}>
                  {job.result_url ? (
                    <a href={job.result_url} target="_blank" rel="noopener noreferrer">Download</a>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
