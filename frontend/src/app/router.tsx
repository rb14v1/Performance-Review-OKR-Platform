import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "../components/AppShell";
import { RequireAuth, RequireRole } from "../components/RequireAuth";
import LoginPage from "../features/auth/LoginPage";
import ObjectivesPage from "../features/okrs/ObjectivesPage";
import ReviewsHome from "../features/reviews/ReviewsHome";
import FeedbackPage from "../features/feedback/FeedbackPage";
import CalibrationPage from "../features/calibration/CalibrationPage";
import TeamDashboardPage from "../features/dashboard/TeamDashboardPage";
import OrgDashboardPage from "../features/dashboard/OrgDashboardPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/okrs" replace />} />
          <Route path="/okrs" element={<ObjectivesPage />} />
          <Route path="/cycles" element={<ReviewsHome />} />
          <Route path="/feedback" element={<FeedbackPage />} />

          <Route element={<RequireRole roles={["hr_admin"]} />}>
            <Route path="/calibration" element={<CalibrationPage />} />
            <Route path="/dashboard/org" element={<OrgDashboardPage />} />
          </Route>

          <Route element={<RequireRole roles={["manager", "hr_admin"]} />}>
            <Route path="/dashboard/team" element={<TeamDashboardPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/okrs" replace />} />
    </Routes>
  );
}
