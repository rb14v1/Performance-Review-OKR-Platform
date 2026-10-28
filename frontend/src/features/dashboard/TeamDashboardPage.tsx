import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { useAsync } from "../../hooks/useAsync";
import { fetchTeamProgress } from "../../api/endpoints/dashboard";
import ProgressBar from "../../components/ProgressBar";

export default function TeamDashboardPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const { data: rows, loading, error } = useAsync(
    () => fetchTeamProgress(selectedId ?? undefined),
    [selectedId]
  );

  return (
    <div>
      <h2>Team Progress</h2>
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
        <div key={row.user_id} className="card">
          <strong>{row.name || row.email}</strong>{" "}
          <span className="muted">({row.objective_count} objective(s))</span>
          <ProgressBar value={row.average_progress_pct} />
        </div>
      ))}
      {rows && rows.length === 0 && <p className="muted">No team members found.</p>}
    </div>
  );
}
