interface Props {
  value: number | string;
}

export default function ProgressBar({ value }: Props) {
  const numeric = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div>
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${numeric}%` }} />
      </div>
      <span className="muted">{numeric.toFixed(1)}%</span>
    </div>
  );
}
