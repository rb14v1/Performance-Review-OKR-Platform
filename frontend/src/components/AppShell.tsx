import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../app/store";

export default function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <nav className="app-nav">
        <h1>Performance &amp; OKR</h1>
        <NavLink to="/okrs">OKRs</NavLink>
        <NavLink to="/cycles">Review Cycles</NavLink>
        <NavLink to="/feedback">360 Feedback</NavLink>
        {(user?.role === "hr_admin") && <NavLink to="/calibration">Calibration</NavLink>}
        {(user?.role === "manager" || user?.role === "hr_admin") && (
          <NavLink to="/dashboard/team">Team Dashboard</NavLink>
        )}
        {user?.role === "hr_admin" && <NavLink to="/dashboard/org">Org Dashboard</NavLink>}
        <hr style={{ margin: "1rem 0", borderColor: "#253866" }} />
        <div className="muted" style={{ color: "#aeb8d6" }}>
          {user?.email} ({user?.role})
        </div>
        <button className="secondary" style={{ marginTop: "0.5rem" }} onClick={logout}>
          Log out
        </button>
      </nav>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
