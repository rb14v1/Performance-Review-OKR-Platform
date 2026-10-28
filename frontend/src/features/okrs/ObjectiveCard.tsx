import { useState } from "react";
import { getObjective } from "../../api/endpoints/okrs";
import ProgressBar from "../../components/ProgressBar";
import KeyResultForm from "./KeyResultForm";
import CheckInForm from "./CheckInForm";
import type { Objective } from "../../types";

export default function ObjectiveCard({
  objective,
  onChanged,
}: {
  objective: Objective;
  onChanged?: () => void;
}) {
  const [detail, setDetail] = useState<Objective | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [openCheckIn, setOpenCheckIn] = useState<number | null>(null);

  async function loadDetail() {
    const data = await getObjective(objective.id);
    setDetail(data);
    onChanged?.();
  }

  async function toggle() {
    if (!expanded) await loadDetail();
    setExpanded(!expanded);
  }

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <strong>{objective.title}</strong>{" "}
          <span className="badge">{objective.status}</span>
          <p className="muted">{objective.owner.email}</p>
        </div>
        <button className="secondary" onClick={toggle}>
          {expanded ? "Hide" : "Details"}
        </button>
      </div>
      <ProgressBar value={objective.progress_pct} />

      {expanded && detail && (
        <div style={{ marginTop: "1rem" }}>
          <h4>Key Results</h4>
          {detail.key_results?.map((kr) => (
            <div key={kr.id} className="card" style={{ background: "#fafbfc" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                  <strong>{kr.title}</strong>{" "}
                  <span className="muted">
                    ({kr.metric_type}, {kr.current_value}/{kr.target_value}
                    {kr.weight ? `, weight ${kr.weight}` : ""})
                  </span>
                </div>
                <button
                  className="secondary"
                  onClick={() => setOpenCheckIn(openCheckIn === kr.id ? null : kr.id)}
                >
                  Check in
                </button>
              </div>
              <ProgressBar value={kr.progress_pct} />
              {openCheckIn === kr.id && (
                <CheckInForm keyResult={kr} onChecked={loadDetail} />
              )}
            </div>
          ))}

          {detail.child_objectives && detail.child_objectives.length > 0 && (
            <>
              <h4>Aligned child objectives</h4>
              {detail.child_objectives.map((child) => (
                <div key={child.id} className="muted">
                  {child.title} - {child.progress_pct}%
                </div>
              ))}
            </>
          )}

          <h4>Add key result</h4>
          <KeyResultForm objectiveId={objective.id} onCreated={loadDetail} />
        </div>
      )}
    </div>
  );
}
