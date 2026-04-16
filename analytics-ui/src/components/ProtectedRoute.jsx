import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Wraps a route so only authenticated users with the right role can access it.
 * If not logged in → redirect to /login
 * If wrong role → redirect to their correct dashboard
 */
export function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    // Redirect to the correct dashboard for this user's role
    const dashboardPath = user?.role === "admin" ? "/admin" : "/department";
    return <Navigate to={dashboardPath} replace />;
  }

  return children;
}
