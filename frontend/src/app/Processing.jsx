import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";

const STEPS = [
  { label: "Ingesting documents", detail: "Parsing 8 files · detecting document types" },
  { label: "Retrieving provisions", detail: "PPA 2007 · BPP Standard Bidding Documents" },
  { label: "Evaluating requirements", detail: "12 requirements · grounded verdicts" },
  { label: "Generating report", detail: "Justifications · overall compliance score" },
];

const STEP_MS = 1600;

export default function Processing() {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (current >= STEPS.length) {
      const t = setTimeout(() => navigate("/app/evaluations/EV-2026-024", { replace: true }), 500);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setCurrent((c) => c + 1), STEP_MS);
    return () => clearTimeout(t);
  }, [current, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center px-5 md:px-7">
      <div className="w-full max-w-[520px]">
        <p className="text-eyebrow text-center text-fg/50">Evaluating submission</p>
        <h1 className="text-subhead mt-3 text-center text-fg" style={{ fontSize: "clamp(26px,2.6vw,38px)" }}>
          Sifting the submission…
        </h1>
        <ol className="mt-12 flex flex-col gap-2">
          {STEPS.map((s, i) => {
            const state = i < current ? "done" : i === current ? "active" : "todo";
            return (
              <li
                key={s.label}
                className={`flex items-center gap-4 border border-dashed px-5 py-4 transition-all duration-500 ${
                  state === "active"
                    ? "border-fg/40 bg-cream"
                    : state === "done"
                      ? "border-[var(--color-border)] bg-cream/50"
                      : "border-fg/10 opacity-45"
                }`}
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                  {state === "done" ? (
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-cream">
                      <Check size={13} />
                    </span>
                  ) : state === "active" ? (
                    <span className="pulse-dot h-3 w-3 rounded-full bg-fg" />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-fg/25" />
                  )}
                </span>
                <div>
                  <div className="text-button text-fg">{s.label}</div>
                  <div className="text-caption text-fg/50" style={{ fontSize: 12.5 }}>
                    {s.detail}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
        <div className="mt-8 h-[3px] w-full overflow-hidden bg-fg/10">
          <div
            className="h-full bg-fg transition-all duration-700"
            style={{
              width: `${(Math.min(current, STEPS.length) / STEPS.length) * 100}%`,
              transitionTimingFunction: "cubic-bezier(0.22,1,0.36,1)",
            }}
          />
        </div>
      </div>
    </div>
  );
}
