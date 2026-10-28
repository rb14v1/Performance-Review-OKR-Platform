import { useState } from "react";
import { useAsync } from "../../hooks/useAsync";
import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { listDirectReports } from "../../api/endpoints/users";
import {
  createManagerReview,
  listManagerReviews,
  submitManagerReview,
  updateManagerReview,
} from "../../api/endpoints/reviews";
import { extractErrorMessage } from "../../api/client";
import type { Paginated, User } from "../../types";

export default function ManagerReviewPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const { data: reportsRaw } = useAsync(() => listDirectReports(), []);
  const reports: User[] = reportsRaw
    ? Array.isArray(reportsRaw)
      ? reportsRaw
      : (reportsRaw as Paginated<User>).results
    : [];

  const {
    data: reviews,
    error,
    reload,
  } = useAsync(() => listManagerReviews(selectedId ?? undefined), [selectedId]);

  const [draftByEmployee, setDraftByEmployee] = useState<Record<number, { rating: string; comments: string }>>(
    {}
  );
  const [formError, setFormError] = useState<string | null>(null);

  function getDraft(employeeId: number) {
    return draftByEmployee[employeeId] || { rating: "", comments: "" };
  }

  async function handleSaveOrSubmit(employeeId: number, submit: boolean) {
    if (!selectedId) return;
    setFormError(null);
    try {
      const existing = reviews?.find((r) => r.employee.id === employeeId);
      let reviewId = existing?.id;
      const draft = getDraft(employeeId);
      if (!existing) {
        const created = await createManagerReview({
          cycle: selectedId,
          employee_id: employeeId,
          draft_rating: draft.rating,
          comments: draft.comments,
        });
        reviewId = created.id;
      } else if (draft.rating || draft.comments) {
        await updateManagerReview(existing.id, {
          draft_rating: draft.rating || existing.draft_rating,
          comments: draft.comments || existing.comments,
        });
      }
      if (submit && reviewId) {
        await submitManagerReview(reviewId);
      }
      reload();
    } catch (err) {
      setFormError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h2>Manager Reviews</h2>
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

      {error && <p className="error-text">{error}</p>}
      {formError && <p className="error-text">{formError}</p>}

      {reports.map((report) => {
        const existing = reviews?.find((r) => r.employee.id === report.id);
        const draft = getDraft(report.id);
        return (
          <div key={report.id} className="card">
            <strong>{report.email}</strong>
            {existing?.submitted_at ? (
              <p className="badge">Submitted</p>
            ) : (
              <form className="stacked" onSubmit={(e) => e.preventDefault()}>
                <label>
                  Draft rating
                  <input
                    value={existing?.draft_rating ?? draft.rating}
                    onChange={(e) =>
                      setDraftByEmployee((prev) => ({
                        ...prev,
                        [report.id]: { ...draft, rating: e.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  Comments
                  <textarea
                    value={existing?.comments ?? draft.comments}
                    onChange={(e) =>
                      setDraftByEmployee((prev) => ({
                        ...prev,
                        [report.id]: { ...draft, comments: e.target.value },
                      }))
                    }
                  />
                </label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button type="button" onClick={() => handleSaveOrSubmit(report.id, false)}>
                    Save draft
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => handleSaveOrSubmit(report.id, true)}
                  >
                    Submit
                  </button>
                </div>
              </form>
            )}
          </div>
        );
      })}
      {reports.length === 0 && <p className="muted">You have no direct reports.</p>}
    </div>
  );
}
