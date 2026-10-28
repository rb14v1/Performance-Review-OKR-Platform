import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { listUsers } from "../../api/endpoints/users";
import { apiClient } from "../../api/client";
import {
  adjustCalibrationEntry,
  createCalibrationEntry,
  createCalibrationSession,
  listCalibrationSessions,
} from "../../api/endpoints/feedback";
import { extractErrorMessage } from "../../api/client";
import type { Department, Paginated, User } from "../../types";

export default function CalibrationPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const { data: departments } = useAsync(async () => {
    const response = await apiClient.get<Paginated<Department> | Department[]>("/departments/");
    return Array.isArray(response.data) ? response.data : response.data.results;
  }, []);
  const { data: usersRaw } = useAsync(() => listUsers(), []);
  const allUsers: User[] = usersRaw
    ? Array.isArray(usersRaw)
      ? usersRaw
      : (usersRaw as Paginated<User>).results
    : [];

  const {
    data: sessions,
    error,
    reload,
  } = useAsync(() => listCalibrationSessions(selectedId ?? undefined), [selectedId]);

  const [departmentId, setDepartmentId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [preRating, setPreRating] = useState("");
  const [sessionIdForEntry, setSessionIdForEntry] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const [adjustments, setAdjustments] = useState<Record<number, { post: string; reason: string }>>({});

  async function handleCreateSession(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setFormError(null);
    try {
      await createCalibrationSession({ cycle: selectedId, department_id: Number(departmentId) });
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  async function handleAddEntry(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await createCalibrationEntry({
        session: Number(sessionIdForEntry),
        employee_id: Number(employeeId),
        pre_rating: preRating,
      });
      setEmployeeId("");
      setPreRating("");
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  async function handleAdjust(entryId: number) {
    const form = adjustments[entryId] || { post: "", reason: "" };
    try {
      await adjustCalibrationEntry(entryId, form.post, form.reason);
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h2>Calibration Board</h2>
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

      <div className="card">
        <h3>Open a calibration session</h3>
        <form className="stacked" onSubmit={handleCreateSession}>
          <label>
            Department
            <select required value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
              <option value="">Select...</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={!selectedId}>
            Create session
          </button>
        </form>
      </div>

      {error && <p className="error-text">{error}</p>}
      {formError && <p className="error-text">{formError}</p>}

      {sessions?.map((session) => (
        <div key={session.id} className="card">
          <strong>{session.department.name}</strong> <span className="badge">{session.status}</span>

          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Pre</th>
                <th>Post</th>
                <th>Reason</th>
                <th>Resolved</th>
                <th>Adjust</th>
              </tr>
            </thead>
            <tbody>
              {session.entries.map((entry) => {
                const form = adjustments[entry.id] || { post: entry.post_rating, reason: entry.adjustment_reason };
                return (
                  <tr key={entry.id}>
                    <td>{entry.employee.email}</td>
                    <td>{entry.pre_rating}</td>
                    <td>{entry.post_rating || "-"}</td>
                    <td>{entry.adjustment_reason}</td>
                    <td>{entry.resolved ? "Yes" : "No"}</td>
                    <td>
                      <input
                        placeholder="post rating"
                        value={form.post}
                        onChange={(e) =>
                          setAdjustments((prev) => ({
                            ...prev,
                            [entry.id]: { ...form, post: e.target.value },
                          }))
                        }
                        style={{ width: 90, marginBottom: 4 }}
                      />
                      <input
                        placeholder="reason"
                        value={form.reason}
                        onChange={(e) =>
                          setAdjustments((prev) => ({
                            ...prev,
                            [entry.id]: { ...form, reason: e.target.value },
                          }))
                        }
                        style={{ width: 120, marginBottom: 4 }}
                      />
                      <button onClick={() => handleAdjust(entry.id)}>Save</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <form className="stacked" onSubmit={handleAddEntry} style={{ marginTop: "0.75rem" }}>
            <input type="hidden" value={session.id} />
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end" }}>
              <label style={{ flex: 1 }}>
                Employee
                <select
                  required
                  value={sessionIdForEntry === String(session.id) ? employeeId : ""}
                  onChange={(e) => {
                    setSessionIdForEntry(String(session.id));
                    setEmployeeId(e.target.value);
                  }}
                >
                  <option value="">Select...</option>
                  {allUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.email}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ flex: 1 }}>
                Pre-calibration rating
                <input
                  value={sessionIdForEntry === String(session.id) ? preRating : ""}
                  onChange={(e) => {
                    setSessionIdForEntry(String(session.id));
                    setPreRating(e.target.value);
                  }}
                />
              </label>
              <button type="submit">Add entry</button>
            </div>
          </form>
        </div>
      ))}
    </div>
  );
}
