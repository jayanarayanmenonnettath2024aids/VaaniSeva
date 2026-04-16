import { createContext, useContext, useState, useCallback } from "react";

const AuthContext = createContext(null);

const API_BASE = "http://localhost:8000";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = sessionStorage.getItem("vaaniseva_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => sessionStorage.getItem("vaaniseva_token") || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Login failed. Please check your credentials.");
        return false;
      }

      sessionStorage.setItem("vaaniseva_token", data.token);
      sessionStorage.setItem("vaaniseva_user", JSON.stringify(data.user));
      setToken(data.token);
      setUser(data.user);
      return data.user;
    } catch {
      setError("Cannot connect to the server. Please ensure the backend is running.");
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch { /* ignore errors */ }
    }
    sessionStorage.removeItem("vaaniseva_token");
    sessionStorage.removeItem("vaaniseva_user");
    setToken(null);
    setUser(null);
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, loading, error, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
