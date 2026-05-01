import { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
  onLogout?: () => void;
  username?: string;
}

export function Layout({ children, onLogout, username }: LayoutProps) {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}>
      <header style={{
        backgroundColor: "#343a40",
        color: "white",
        padding: "12px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <h1 style={{ margin: 0, fontSize: "18px" }}>Report Processing System</h1>
        {username && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span>{username}</span>
            {onLogout && (
              <button
                onClick={onLogout}
                style={{ background: "none", border: "1px solid white", color: "white", padding: "4px 12px", borderRadius: "4px", cursor: "pointer" }}
              >
                Logout
              </button>
            )}
          </div>
        )}
      </header>
      <main style={{ maxWidth: "1024px", margin: "0 auto", padding: "24px 16px" }}>
        {children}
      </main>
    </div>
  );
}
