import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { listObjectives, createObjective } from "../../api/endpoints/okrs";
import { extractErrorMessage } from "../../api/client";
import ObjectiveCard from "./ObjectiveCard";

export default function ObjectivesPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const {
    data: objectives,
    loading,
    error,
    reload,
  } = useAsync(() => listObjectives(selectedId ?? undefined), [selectedId]);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [parentId, setParentId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await createObjective({
        cycle: selectedId,
        title,
        description,
        parent_objective: parentId ? Number(parentId) : null,
      });
      setTitle("");
      setDescription("");
      setParentId("");
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Objectives &amp; Key Results</h2>

      <label>
        Cycle:{" "}
        <select
          value={selectedId ?? ""}
          onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
        >
          {cycles.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.status})
            </option>
          ))}
        </select>
      </label>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h3>New objective</h3>
        <form className="stacked" onSubmit={handleCreate}>
          <label>
            Title
            <input required value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            Description
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <label>
            Align under parent objective (optional, by ID)
            <input value={parentId} onChange={(e) => setParentId(e.target.value)} />
          </label>
          {formError && <p className="error-text">{formError}</p>}
          <button type="submit" disabled={submitting || !selectedId}>
            {submitting ? "Creating..." : "Create objective"}
          </button>
        </form>
      </div>

      {loading && <p>Loading objectives...</p>}
      {error && <p className="error-text">{error}</p>}
      {objectives?.map((o) => (
        <ObjectiveCard key={o.id} objective={o} onChanged={reload} />
      ))}
      {objectives && objectives.length === 0 && <p className="muted">No objectives yet for this cycle.</p>}
    </div>
  );
}
