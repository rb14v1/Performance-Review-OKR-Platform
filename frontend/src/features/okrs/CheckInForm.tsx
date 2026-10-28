import { useState } from "react";
import { createCheckIn } from "../../api/endpoints/okrs";
import { extractErrorMessage } from "../../api/client";
import type { KeyResult } from "../../types";

export default function CheckInForm({
  keyResult,
  onChecked,
}: {
  keyResult: KeyResult;
  onChecked: () => void;
}) {
  const [value, setValue] = useState(keyResult.current_value);
  const [confidence, setConfidence] = useState("medium");
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createCheckIn({
        key_result: keyResult.id,
        value: Number(value),
        confidence_level: confidence,
        comment,
      });
      setComment("");
      onChecked();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="stacked" onSubmit={handleSubmit} style={{ marginTop: "0.5rem" }}>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end" }}>
        <label style={{ flex: 1 }}>
          {keyResult.metric_type === "boolean" ? "Done? (1/0)" : "New value"}
          <input
            type="number"
            step="any"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </label>
        <label style={{ flex: 1 }}>
          Confidence
          <select value={confidence} onChange={(e) => setConfidence(e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
      </div>
      <label>
        Comment
        <input value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      {error && <p className="error-text">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Checking in..." : "Check in"}
      </button>
    </form>
  );
}
