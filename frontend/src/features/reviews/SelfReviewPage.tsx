import { useEffect, useState } from "react";
import { useSelectedCycle } from "../../hooks/useSelectedCycle";
import { listSelfReviews, submitSelfReview, createSelfReview, updateSelfReview, listRatings, acknowledgeRating } from "../../api/endpoints/reviews";
import { extractErrorMessage } from "../../api/client";
import type { Rating, SelfReview } from "../../types";

export default function SelfReviewPage() {
  const { cycles, selectedId, setSelectedId } = useSelectedCycle();
  const [existing, setExisting] = useState<SelfReview | null>(null);
  const [accomplishments, setAccomplishments] = useState("");
  const [challenges, setChallenges] = useState("");
  const [selfRating, setSelfRating] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [myRating, setMyRating] = useState<Rating | null>(null);

  useEffect(() => {
    if (!selectedId) return;
    listSelfReviews(selectedId).then((reviews) => {
      const mine = reviews[0] || null;
      setExisting(mine);
      setAccomplishments(mine?.accomplishments || "");
      setChallenges(mine?.challenges || "");
      setSelfRating(mine?.self_rating || "");
    });
    listRatings(selectedId).then((ratings) => setMyRating(ratings[0] || null));
  }, [selectedId]);

  async function handleAcknowledge() {
    if (!myRating) return;
    const updated = await acknowledgeRating(myRating.id);
    setMyRating(updated);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedId) return;
    setSaving(true);
    setError(null);
    try {
      const saved = existing
        ? await updateSelfReview(existing.id, { accomplishments, challenges, self_rating: selfRating })
        : await createSelfReview({ cycle: selectedId, accomplishments, challenges, self_rating: selfRating });
      setExisting(saved);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    if (!existing) return;
    setError(null);
    try {
      const submitted = await submitSelfReview(existing.id);
      setExisting(submitted);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h2>Self Review</h2>
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
        {existing?.submitted_at && (
          <p className="badge">Submitted {new Date(existing.submitted_at).toLocaleString()}</p>
        )}
        <form className="stacked" onSubmit={handleSave}>
          <label>
            Accomplishments
            <textarea
              rows={4}
              value={accomplishments}
              onChange={(e) => setAccomplishments(e.target.value)}
              disabled={!!existing?.submitted_at}
            />
          </label>
          <label>
            Challenges
            <textarea
              rows={4}
              value={challenges}
              onChange={(e) => setChallenges(e.target.value)}
              disabled={!!existing?.submitted_at}
            />
          </label>
          <label>
            Self rating
            <input
              value={selfRating}
              onChange={(e) => setSelfRating(e.target.value)}
              disabled={!!existing?.submitted_at}
            />
          </label>
          {error && <p className="error-text">{error}</p>}
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" disabled={saving || !!existing?.submitted_at}>
              {saving ? "Saving..." : "Save draft"}
            </button>
            {existing && !existing.submitted_at && (
              <button type="button" className="secondary" onClick={handleSubmit}>
                Submit self-review
              </button>
            )}
          </div>
        </form>
      </div>

      {myRating?.final_rating && (
        <div className="card">
          <h3>Your final rating</h3>
          <p>
            <span className="badge">{myRating.final_rating}</span>{" "}
            <span className="muted">(source: {myRating.rating_source})</span>
          </p>
          {myRating.acknowledged_by_employee ? (
            <p className="muted">
              Acknowledged {myRating.acknowledged_at && new Date(myRating.acknowledged_at).toLocaleString()}
            </p>
          ) : (
            <button onClick={handleAcknowledge}>Acknowledge rating</button>
          )}
        </div>
      )}
    </div>
  );
}
