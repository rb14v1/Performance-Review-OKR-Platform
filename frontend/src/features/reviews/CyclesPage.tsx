import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../app/store";
import { createCycle, listCycles, transitionCycle } from "../../api/endpoints/reviews";
import { extractErrorMessage } from "../../api/client";
import type { CycleStatus } from "../../types";

const ORDER: CycleStatus[] = [
  "draft",
  "self_review",
  "manager_review",
  "peer_feedback",
  "calibration",
  "closed",
];

function nextStatus(current: CycleStatus): CycleStatus | null {
  const idx = ORDER.indexOf(current);
  return idx >= 0 && idx < ORDER.length - 1 ? ORDER[idx + 1] : null;
}

export default function CyclesPage() {
  const { user } = useAuth();
  const { data: cycles, loading, error, reload } = useAsync(() => listCycles(), []);

  const [name, setName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  const [overrideReasonByCycle, setOverrideReasonByCycle] = useState<Record<number, string>>({});
  const [transitionError, setTransitionError] = useState<Record<number, string>>({});

  const isHrAdmin = user?.role === "hr_admin";

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateError(null);
    try {
      await createCycle({ name, start_date: startDate, end_date: endDate });
      setName("");
      setStartDate("");
      setEndDate("");
      reload();
    } catch (err) {
      setCreateError(extractErrorMessage(err));
    }
  }

  async function handleTransition(cycleId: number, target: CycleStatus) {
    setTransitionError((prev) => ({ ...prev, [cycleId]: "" }));
    try {
      await transitionCycle(cycleId, target, overrideReasonByCycle[cycleId]);
      reload();
    } catch (err) {
      setTransitionError((prev) => ({ ...prev, [cycleId]: extractErrorMessage(err) }));
    }
  }

  return (
    <div>
      <h2>Review Cycles</h2>

      {isHrAdmin && (
        <div className="card">
          <h3>New cycle</h3>
          <form className="stacked" onSubmit={handleCreate}>
            <label>
              Name
              <input required value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <label style={{ flex: 1 }}>
                Start date
                <input type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </label>
              <label style={{ flex: 1 }}>
                End date
                <input type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </label>
            </div>
            {createError && <p className="error-text">{createError}</p>}
            <button type="submit">Create cycle</button>
          </form>
        </div>
      )}

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {cycles?.map((cycle) => {
        const target = nextStatus(cycle.status);
        return (
          <div key={cycle.id} className="card">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{cycle.name}</strong>
              <span className="badge">{cycle.status.replace("_", " ")}</span>
            </div>
            <p className="muted">
              {cycle.start_date} &rarr; {cycle.end_date}
            </p>
            {isHrAdmin && target && (
              <div>
                <label>
                  Override reason (only needed to force calibration/close early)
                  <input
                    value={overrideReasonByCycle[cycle.id] || ""}
                    onChange={(e) =>
                      setOverrideReasonByCycle((prev) => ({ ...prev, [cycle.id]: e.target.value }))
                    }
                  />
                </label>
                <button onClick={() => handleTransition(cycle.id, target)}>
                  Advance to "{target.replace("_", " ")}"
                </button>
                {transitionError[cycle.id] && (
                  <p className="error-text">{transitionError[cycle.id]}</p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
