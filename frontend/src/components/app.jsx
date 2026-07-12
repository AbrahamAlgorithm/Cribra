import { FileText } from "lucide-react";

export function StatusBadge({ status }) {
  const styles = {
    Compliant: "bg-[#e2efe6] text-[#166237] border-[#166237]/25",
    Missing: "bg-[#f6e3e0] text-[#96291c] border-[#96291c]/25",
    "Needs Review": "bg-[#f5ecd8] text-[#8a5a13] border-[#8a5a13]/25",
  };
  return (
    <span
      className={`text-eyebrow inline-flex items-center gap-2 whitespace-nowrap border px-2 py-1 ${styles[status] || ""}`}
    >
      <span
        className="h-[6px] w-[6px] rounded-full"
        style={{
          background:
            status === "Compliant" ? "#1b7a43" : status === "Missing" ? "#c03a2b" : "#b7791f",
        }}
      />
      {status}
    </span>
  );
}

export function DocTypeBadge({ type }) {
  return (
    <span className="text-eyebrow inline-block whitespace-nowrap border border-fg/15 bg-fg/5 px-2 py-[3px] text-fg/60">
      {type}
    </span>
  );
}

export function FileListItem({ file, onRemove }) {
  return (
    <li className="flex items-center justify-between gap-4 border-b border-dashed border-fg/15 px-4 py-3 last:border-0">
      <div className="flex min-w-0 items-center gap-3">
        <FileText size={16} className="shrink-0 text-fg/40" />
        <span className="text-caption truncate text-fg">{file.name}</span>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <DocTypeBadge type={file.type} />
        <span className="text-eyebrow text-fg/45">{file.size}</span>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label={`Remove ${file.name}`}
            className="text-fg/40 transition-colors hover:text-missing"
          >
            ✕
          </button>
        )}
      </div>
    </li>
  );
}

export function ScoreRing({ score, size = 132 }) {
  const r = size / 2 - 9;
  const circ = 2 * Math.PI * r;
  const color = score >= 80 ? "#1b7a43" : score >= 60 ? "#b7791f" : "#c03a2b";
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(26,23,20,0.1)" strokeWidth="8" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - score / 100)}
          className="ring-animate"
          style={{ "--ring-circ": circ }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-serif text-[34px] leading-none text-fg">{score}%</span>
        <span className="text-eyebrow mt-1 text-fg/45">Compliant</span>
      </div>
    </div>
  );
}

export function StatTile({ label, value, hint }) {
  return (
    <div className="relative border border-dashed border-[var(--color-border)] bg-cream/70 p-6">
      <div className="text-eyebrow text-fg/50">{label}</div>
      <div className="mt-4 font-serif text-[52px] leading-none text-fg">{value}</div>
      {hint && <div className="text-caption mt-3 text-fg/50">{hint}</div>}
    </div>
  );
}

export function Stepper({ step }) {
  const steps = ["Tender Requirements", "Contractor Submission"];
  return (
    <ol className="flex items-center gap-3">
      {steps.map((s, i) => {
        const n = i + 1;
        const state = n < step ? "done" : n === step ? "active" : "todo";
        return (
          <li key={s} className="flex items-center gap-3">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-eyebrow ${
                state === "active"
                  ? "bg-fg text-cream"
                  : state === "done"
                    ? "bg-accent text-cream"
                    : "border border-fg/25 text-fg/45"
              }`}
            >
              {state === "done" ? "✓" : n}
            </span>
            <span className={`text-eyebrow ${state === "active" ? "text-fg" : "text-fg/45"}`}>{s}</span>
            {i < steps.length - 1 && <span className="h-px w-10 bg-fg/20" aria-hidden="true" />}
          </li>
        );
      })}
    </ol>
  );
}
