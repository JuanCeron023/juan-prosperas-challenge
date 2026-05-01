import { LoginForm } from "../components/LoginForm";
import { useAuth } from "../hooks/useAuth";

interface LoginPageProps {
  onAuthenticated: () => void;
}

export function LoginPage({ onAuthenticated }: LoginPageProps) {
  const { login, register, loading, error, authenticated } = useAuth();

  if (authenticated) {
    onAuthenticated();
  }

  const handleLogin = async (username: string, password: string) => {
    await login(username, password);
    onAuthenticated();
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", padding: "20px" }}>
      <LoginForm onLogin={handleLogin} onRegister={register} loading={loading} error={error} />
    </div>
  );
}
