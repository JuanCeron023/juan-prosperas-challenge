import { useEffect } from "react";

interface ToastProps {
  message: string | null;
  type: "success" | "error";
  onClose: () => void;
}

export function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(onClose, 5000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);

  if (!message) return null;

  const styles = {
    success: { bg: "#d4edda", text: "#155724", border: "#c3e6cb" },
    error: { bg: "#f8d7da", text: "#721c24", border: "#f5c6cb" },
  };

  const s = styles[type];

  return (
    <div
      role="alert"
      style={{
        position: "fixed",
        top: "20px",
        right: "20px",
        padding: "12px 24px",
        borderRadius: "4px",
        backgroundColor: s.bg,
        color: s.text,
        border: `1px solid ${s.border}`,
        zIndex: 1000,
        maxWidth: "400px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{message}</span>
        <button
          onClick={onClose}
          style={{ background: "none", border: "none", cursor: "pointer", marginLeft: "12px", fontSize: "16px", color: s.text }}
          aria-label="Close notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}
