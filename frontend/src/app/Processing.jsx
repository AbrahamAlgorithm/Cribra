import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Check, AlertTriangle } from "lucide-react";
import { getStatus } from "../lib/api.js";

// Mirrors the real Evaluation.status lifecycle (app/models/domain.py).
// "retrieving" is a defined status value but never actually set by the
// backend (Milestone 5 finding — retrieval happens inside each per-
// requirement 4B call, not as one distinct global step), so it's omitted
// here rather than shown as a step that never lights up.
const STEPS = [
  { key: "ingesting", label: "Ingesting documents", detail: "Extracting text, classifying document types" },
  { key: "evaluating", label: "Evaluating requirements", detail: "Certificate rules + RAG-grounded reasoning" },
  { key: "generating_report", label: "Generating report", detail: "Justifications, citations, compliance score" },
];

const POLL_MS = 3000;

function stepIndexFor(status) {
  if (status === "pending" || status === "ingesting") return 0;
  if (status === "retrieving" || status === "evaluating") return 1;
  if (status === "generating_report") return 2;
  if (status === "complete") return STEPS.length;
  return 0;
}

export default function Processing() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const evaluationId = searchParams.get("id");
  const [current, setCurrent] = useState(0);
  const [failed, setFailed] = useState(false);
  const [pollError, setPollError] = useState(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!evaluationId) return undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const { status } = await getStatus(evaluationId);
        if (cancelled) return;
        if (status === "failed") {
          setFailed(true);
          return;
        }
        if (status === "complete") {
          setCurrent(STEPS.length);
          navigate(`/app/evaluations/${evaluationId}`, { replace: true });
          return;
        }
        setCurrent(stepIndexFor(status));
        timeoutRef.current = setTimeout(poll, POLL_MS);
      } catch (err) {
        if (!cancelled) setPollError(err.message);
      }
    };

    poll();
    return () => {
      cancelled = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [evaluationId, navigate]);

  if (!evaluationId) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5 text-center">
        <p className="text-caption text-fg/60">
          No evaluation in progress. <Link to="/app/evaluations/new" className="underline">Start a new one</Link>.
        </p>
      </div>
    );
  }

  if (failed) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5 text-center">
        <div>
          <AlertTriangle size={28} className="mx-auto text-[#96291c]" />
          <p className="text-subhead mt-4 text-fg">Evaluation failed</p>
          <p className="text-caption mt-2 text-fg/60">
            Something went wrong while processing this submission. Check the backend logs.
          </p>
          <Link to="/app/evaluations/new" className="text-button mt-6 inline-block underline">
            Start a new evaluation
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5 md:px-7">
      <div className="w-full max-w-[520px]">
        <p className="text-eyebrow text-center text-fg/50">Evaluating submission</p>
        <h1 className="text-subhead mt-3 text-center text-fg" style={{ fontSize: "clamp(26px,2.6vw,38px)" }}>
          Sifting the submission…
        </h1>
        {pollError && (
          <p className="text-caption mt-3 text-center text-[#96291c]">Lost connection: {pollError}</p>
        )}
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
        <p className="text-caption mt-6 text-center text-fg/40" style={{ fontSize: 12 }}>
          Real evaluations can take 40–90 seconds or more depending on submission size.
        </p>
      </div>
    </div>
  );
}
