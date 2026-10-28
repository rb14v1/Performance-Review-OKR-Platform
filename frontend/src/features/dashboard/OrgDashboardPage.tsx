import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { useAsync } from "../../hooks/useAsync";
import { fetchOrgProgress } from "../../api/endpoints/dashboard";
import ProgressBar from "../../components/ProgressBar";

export default function OrgDashboardPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const { data: rows, loading, error } = useAsync(
    () => fetchOrgProgress(selectedId ?? undefined),
    [selectedId]
  );

  return (
    <div>
      <h2>Org-wide Progress</h2>
      <label>
        Cycle:{" "}
        <select
          value={selectedId ?? ""}
          onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">All cycles</option>
          {cycles.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.status})
            </option>
          ))}
        </select>
      </label>

      {loading && <p>Loading...</p>}
      {error && <p className="error-text">{error}</p>}

      {rows?.map((row) => (
        <div key={row.department_id} className="card">
          <strong>{row.department_name}</strong>{" "}
          <span className="muted">({row.objective_count} objective(s))</span>
          <ProgressBar value={row.average_progress_pct} />
        </div>
      ))}
      {rows && rows.length === 0 && <p className="muted">No departments found.</p>}
    </div>
  );
}
