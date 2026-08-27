import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, ArrowRight, ArrowLeft, Play, Loader2 } from "lucide-react";
import {
  getDefaultRequirements,
  createManualEvaluation,
  setEvaluationDate,
  submitDocuments,
  runEvaluate,
} from "../lib/api.js";
import { Stepper, FileListItem } from "../components/app.jsx";
import { CornerFrame, PrimaryButton, FrameButton, Reveal } from "../components/ui.jsx";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StepOne({
  requirements,
  checkedIds,
  onToggle,
  loading,
  error,
  creating,
  createError,
  evaluationDate,
  onEvaluationDateChange,
  onNext,
}) {
  const checkedCount = checkedIds.size;
  return (
    <>
      <CornerFrame className="mt-10 flex flex-col gap-3 bg-fg p-6 text-cream">
        <span className="text-eyebrow text-cream/60">
          {loading ? "Loading…" : `Default checklist · ${checkedCount} of ${requirements.length} selected`}
        </span>
        <span className="text-pullquote" style={{ fontSize: 22 }}>
          BPP / PPA 2007 Standard Checklist
        </span>
        <span className="text-caption text-cream/65">
          The standard checklist drawn from the BPP/PPA 2007 framework.
        </span>
      </CornerFrame>

      <CornerFrame className="mt-4 flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <label htmlFor="evaluation-date" className="text-eyebrow text-fg/55">
            Evaluation date
          </label>
          <p className="text-caption mt-1 text-fg/50" style={{ fontSize: 12.5 }}>
            Certificate expiry is checked against this date, not necessarily today.
          </p>
        </div>
        <input
          id="evaluation-date"
          type="date"
          value={evaluationDate}
          onChange={(e) => onEvaluationDateChange(e.target.value)}
          className="text-caption border border-dashed border-fg/25 bg-cream/60 px-3 py-2 text-fg focus:border-fg/50 focus:outline-none"
        />
      </CornerFrame>

      {error && (
        <p className="text-caption mt-4 text-[#96291c]">
          Couldn't reach the backend ({error}). Is it running at{" "}
          <code>uvicorn app.main:app --reload</code>?
        </p>
      )}

      {requirements.length > 0 && (
        <div className="mt-10">
          <h2 className="text-eyebrow text-fg/55">Select the requirements to check</h2>
          <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
            {requirements.map((r, i) => (
              <li
                key={r.id}
                className="flex items-baseline gap-4 border-b border-dashed border-fg/12 px-5 py-3 last:border-0"
              >
                <span className="text-eyebrow shrink-0 text-fg/40">{String(i + 1).padStart(2, "0")}</span>
                <label className="flex flex-1 cursor-pointer items-baseline gap-4">
                  <span className={`text-caption ${checkedIds.has(r.id) ? "text-fg" : "text-fg/40 line-through"}`}>
                    {r.name}
                  </span>
                  <input
                    type="checkbox"
                    className="ml-auto h-4 w-4 shrink-0 cursor-pointer accent-fg"
                    checked={checkedIds.has(r.id)}
                    onChange={() => onToggle(r.id)}
                  />
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}

      {createError && <p className="text-caption mt-4 text-[#96291c]">{createError}</p>}

      <div className="mt-10 flex justify-end">
        <PrimaryButton
          onClick={onNext}
          className={requirements.length === 0 || checkedCount === 0 || creating ? "pointer-events-none opacity-40" : ""}
        >
          <span className="inline-flex items-center gap-2">
            {creating ? <Loader2 size={14} className="animate-spin" /> : null}
            {creating ? "Starting…" : "Next: Contractor Submission"}
            {!creating && <ArrowRight size={15} />}
          </span>
        </PrimaryButton>
      </div>
    </>
  );
}

function StepTwo({ files, setFiles, onBack, onRun, running, error }) {
  const addFiles = (fileList) => {
    setFiles((prev) => [...prev, ...Array.from(fileList)]);
  };

  return (
    <>
      <CornerFrame className="mt-10 p-2">
        <label className="flex w-full cursor-pointer flex-col items-center justify-center gap-3 border border-dashed border-fg/20 bg-cream/50 px-6 py-14 transition-colors hover:bg-cream">
          <UploadCloud size={28} className="text-fg/40" />
          <span className="text-body text-fg/70" style={{ fontSize: 18 }}>
            Click to choose the contractor's documents
          </span>
          <span className="text-caption text-fg/45">PDF, DOCX, JPG, PNG</span>
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
        </label>
      </CornerFrame>

      {files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-eyebrow text-fg/55">Submission · {files.length} file(s)</h2>
          <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
            {files.map((f, i) => (
              <FileListItem
                key={`${f.name}-${i}`}
                file={{ name: f.name, type: f.name.split(".").pop().toUpperCase(), size: formatSize(f.size) }}
                onRemove={() => setFiles(files.filter((_, j) => j !== i))}
              />
            ))}
          </ul>
        </div>
      )}

      {error && <p className="text-caption mt-4 text-[#96291c]">{error}</p>}

      <div className="mt-10 flex items-center justify-between">
        <FrameButton onClick={onBack}>
          <span className="inline-flex items-center gap-2">
            <ArrowLeft size={15} /> Back
          </span>
        </FrameButton>
        <PrimaryButton
          onClick={onRun}
          className={files.length === 0 || running ? "pointer-events-none opacity-40" : ""}
        >
          <span className="inline-flex items-center gap-2">
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? "Starting…" : "Run Evaluation"}
          </span>
        </PrimaryButton>
      </div>
    </>
  );
}

export default function NewEvaluation() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [requirements, setRequirements] = useState([]);
  const [checkedIds, setCheckedIds] = useState(new Set());
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluation, setEvaluation] = useState(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [files, setFiles] = useState([]);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState(null);
  const [evaluationDate, setEvaluationDateInput] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    let cancelled = false;
    getDefaultRequirements()
      .then((reqs) => {
        if (cancelled) return;
        setRequirements(reqs);
        setCheckedIds(new Set(reqs.map((r) => r.id)));
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleRequirement = (id) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleNext = async () => {
    setCreating(true);
    setCreateError(null);
    try {
      const selected = requirements
        .filter((r) => checkedIds.has(r.id))
        .map((r) => ({ name: r.name, description: r.description, is_mandatory: r.is_mandatory, source: r.source }));
      const ev = await createManualEvaluation(selected);
      // Explicit even when it matches today's default — reproducibility
      // matters here (Milestone 6: a fixed, documented evaluation date
      // across all test submissions), not just "whatever day this was run."
      const dated = await setEvaluationDate(ev.id, evaluationDate);
      setEvaluation(dated);
      setStep(2);
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setRunError(null);
    try {
      await submitDocuments(evaluation.id, files);
      await runEvaluate(evaluation.id);
      navigate(`/app/evaluations/processing?id=${evaluation.id}`);
    } catch (err) {
      setRunError(err.message);
      setRunning(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <p className="text-eyebrow text-fg/50">New evaluation</p>
        <h1 className="text-subhead mt-2 text-fg" style={{ fontSize: "clamp(28px,3vw,42px)" }}>
          {step === 1 ? "Tender requirements" : "Contractor submission"}
        </h1>
        <div className="mt-8">
          <Stepper step={step} />
        </div>
      </Reveal>
      {step === 1 ? (
        <StepOne
          requirements={requirements}
          checkedIds={checkedIds}
          onToggle={toggleRequirement}
          loading={loading}
          error={loadError}
          creating={creating}
          createError={createError}
          evaluationDate={evaluationDate}
          onEvaluationDateChange={setEvaluationDateInput}
          onNext={handleNext}
        />
      ) : (
        <StepTwo
          files={files}
          setFiles={setFiles}
          onBack={() => setStep(1)}
          onRun={handleRun}
          running={running}
          error={runError}
        />
      )}
    </div>
  );
}
