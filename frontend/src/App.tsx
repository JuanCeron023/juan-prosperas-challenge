import { useState } from "react";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { isAuthenticated, clearToken } from "./api/client";

function App() {
  const [loggedIn, setLoggedIn] = useState(isAuthenticated());
  const [username, setUsername] = useState("");

  const handleAuthenticated = () => {
    setLoggedIn(true);
  };

  const handleLogout = () => {
    clearToken();
    setLoggedIn(false);
    setUsername("");
  };

  if (!loggedIn) {
    return <LoginPage onAuthenticated={handleAuthenticated} />;
  }

  return <DashboardPage onLogout={handleLogout} username={username} />;
}

export default App;
