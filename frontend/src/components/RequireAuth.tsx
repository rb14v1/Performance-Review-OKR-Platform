import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../app/store";
import type { Role } from "../types";

export function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function RequireRole({ roles }: { roles: Role[] }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <p>You do not have access to this page.</p>;
  return <Outlet />;
}
