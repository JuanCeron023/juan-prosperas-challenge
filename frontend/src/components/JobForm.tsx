import { useState, FormEvent } from "react";
import { apiRequest } from "../api/client";
import { JobCreatePayload } from "../types";

interface JobFormProps {
  onJobCreated: () => void;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
}

export function JobForm({ onJobCreated, onError, onSuccess }: JobFormProps) {
  const [reportType, setReportType] = useState<"sales" | "inventory" | "analytics">("sales");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [format, setFormat] = useState<"csv" | "pdf" | "json">("csv");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!startDate) newErrors.startDate = "Start date is required";
    if (!endDate) newErrors.endDate = "End date is required";
    if (startDate && endDate && startDate > endDate) {
      newErrors.endDate = "End date must be after start date";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const payload: JobCreatePayload = {
        report_type: reportType,
        date_range: { start_date: startDate, end_date: endDate },
        format,
      };
      await apiRequest("/jobs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      onSuccess("Report job created successfully");
      onJobCreated();
      // Reset form
      setStartDate("");
      setEndDate("");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setLoading(false);
    }
  };

  const fieldStyle = { width: "100%", padding: "8px", boxSizing: "border-box" as const };
  const errorStyle = { color: "#dc3545", fontSize: "12px", marginTop: "4px" };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "24px" }}>
      <h3>Create Report</h3>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
        <div>
          <label htmlFor="reportType" style={{ display: "block", marginBottom: "4px" }}>Report Type</label>
          <select id="reportType" value={reportType} onChange={(e) => setReportType(e.target.value as "sales" | "inventory" | "analytics")} style={fieldStyle}>
            <option value="sales">Sales</option>
            <option value="inventory">Inventory</option>
            <option value="analytics">Analytics</option>
          </select>
        </div>

        <div>
          <label htmlFor="format" style={{ display: "block", marginBottom: "4px" }}>Format</label>
          <select id="format" value={format} onChange={(e) => setFormat(e.target.value as "csv" | "pdf" | "json")} style={fieldStyle}>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
            <option value="json">JSON</option>
          </select>
        </div>

        <div>
          <label htmlFor="startDate" style={{ display: "block", marginBottom: "4px" }}>Start Date</label>
          <input id="startDate" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={fieldStyle} />
          {errors.startDate && <div style={errorStyle}>{errors.startDate}</div>}
        </div>

        <div>
          <label htmlFor="endDate" style={{ display: "block", marginBottom: "4px" }}>End Date</label>
          <input id="endDate" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={fieldStyle} />
          {errors.endDate && <div style={errorStyle}>{errors.endDate}</div>}
        </div>
      </div>

      <button type="submit" disabled={loading} style={{ marginTop: "12px", padding: "10px 24px", cursor: "pointer" }}>
        {loading ? "Creating..." : "Create Report"}
      </button>
    </form>
  );
}
