import { useState } from "react";
import { createKeyResult } from "../../api/endpoints/okrs";
import { extractErrorMessage } from "../../api/client";

export default function KeyResultForm({
  objectiveId,
  onCreated,
}: {
  objectiveId: number;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [metricType, setMetricType] = useState("number");
  const [startValue, setStartValue] = useState("0");
  const [targetValue, setTargetValue] = useState("100");
  const [weight, setWeight] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createKeyResult({
        objective: objectiveId,
        title,
        metric_type: metricType,
        start_value: Number(startValue),
        target_value: Number(targetValue),
        current_value: Number(startValue),
        weight: weight ? Number(weight) : null,
      });
      setTitle("");
      setWeight("");
      onCreated();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="stacked" onSubmit={handleSubmit}>
      <label>
        Key result title
        <input required value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <label style={{ flex: 1 }}>
          Metric type
          <select value={metricType} onChange={(e) => setMetricType(e.target.value)}>
            <option value="number">Number</option>
            <option value="percentage">Percentage</option>
            <option value="boolean">Boolean</option>
            <option value="currency">Currency</option>
          </select>
        </label>
        <label style={{ flex: 1 }}>
          Start value
          <input type="number" step="any" value={startValue} onChange={(e) => setStartValue(e.target.value)} />
        </label>
        <label style={{ flex: 1 }}>
          Target value
          <input type="number" step="any" value={targetValue} onChange={(e) => setTargetValue(e.target.value)} />
        </label>
        <label style={{ flex: 1 }}>
          Weight (optional)
          <input type="number" step="any" value={weight} onChange={(e) => setWeight(e.target.value)} />
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Adding..." : "Add key result"}
      </button>
    </form>
  );
}
