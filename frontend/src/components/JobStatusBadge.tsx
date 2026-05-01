import { JobStatus, STATUS_COLORS } from "../types";

const BADGE_STYLES: Record<string, { bg: string; text: string }> = {
  yellow: { bg: "#fff3cd", text: "#856404" },
  blue: { bg: "#cce5ff", text: "#004085" },
  green: { bg: "#d4edda", text: "#155724" },
  red: { bg: "#f8d7da", text: "#721c24" },
};

interface JobStatusBadgeProps {
  status: JobStatus;
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const color = STATUS_COLORS[status];
  const style = BADGE_STYLES[color] || BADGE_STYLES.yellow;

  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 12px",
        borderRadius: "12px",
        fontSize: "12px",
        fontWeight: 600,
        backgroundColor: style.bg,
        color: style.text,
      }}
      role="status"
      aria-label={`Status: ${status}`}
    >
      {status}
    </span>
  );
}
