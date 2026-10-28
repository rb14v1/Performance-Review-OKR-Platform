import { useState } from "react";
import { useAuth } from "../../app/store";
import CyclesPage from "./CyclesPage";
import SelfReviewPage from "./SelfReviewPage";
import ManagerReviewPage from "./ManagerReviewPage";

type Tab = "cycles" | "self" | "manager";

export default function ReviewsHome() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("cycles");
  const canManagerReview = user?.role === "manager" || user?.role === "hr_admin";

  return (
    <div>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button className={tab === "cycles" ? "" : "secondary"} onClick={() => setTab("cycles")}>
          Cycles
        </button>
        <button className={tab === "self" ? "" : "secondary"} onClick={() => setTab("self")}>
          Self Review
        </button>
        {canManagerReview && (
          <button className={tab === "manager" ? "" : "secondary"} onClick={() => setTab("manager")}>
            Manager Review
          </button>
        )}
      </div>
      {tab === "cycles" && <CyclesPage />}
      {tab === "self" && <SelfReviewPage />}
      {tab === "manager" && canManagerReview && <ManagerReviewPage />}
    </div>
  );
}
