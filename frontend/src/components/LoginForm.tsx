import { useState, FormEvent } from "react";

interface LoginFormProps {
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, password: string) => Promise<void>;
  loading: boolean;
  error: string | null;
}

export function LoginForm({ onLogin, onRegister, loading, error }: LoginFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (isRegisterMode) {
        await onRegister(username, password);
        setIsRegisterMode(false);
      } else {
        await onLogin(username, password);
      }
    } catch {
      // Error is handled by the hook
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 400, margin: "0 auto" }}>
      <h2>{isRegisterMode ? "Register" : "Login"}</h2>

      {error && (
        <div style={{ color: "#dc3545", padding: "8px", marginBottom: "12px", background: "#f8d7da", borderRadius: "4px" }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: "12px" }}>
        <label htmlFor="username" style={{ display: "block", marginBottom: "4px" }}>Username</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={3}
          style={{ width: "100%", padding: "8px", boxSizing: "border-box" }}
        />
      </div>

      <div style={{ marginBottom: "12px" }}>
        <label htmlFor="password" style={{ display: "block", marginBottom: "4px" }}>Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          style={{ width: "100%", padding: "8px", boxSizing: "border-box" }}
        />
      </div>

      <button type="submit" disabled={loading} style={{ width: "100%", padding: "10px", cursor: "pointer" }}>
        {loading ? "Loading..." : isRegisterMode ? "Register" : "Login"}
      </button>

      <p style={{ textAlign: "center", marginTop: "12px" }}>
        <button type="button" onClick={() => setIsRegisterMode(!isRegisterMode)} style={{ background: "none", border: "none", color: "#007bff", cursor: "pointer" }}>
          {isRegisterMode ? "Already have an account? Login" : "Don't have an account? Register"}
        </button>
      </p>
    </form>
  );
}
