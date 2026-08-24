import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, ArrowRight, ArrowLeft, Play, Loader2 } from "lucide-react";
import { createDefaultEvaluation, submitDocuments, runEvaluate } from "../lib/api.js";
import { Stepper, FileListItem } from "../components/app.jsx";
import { CornerFrame, PrimaryButton, FrameButton, Reveal } from "../components/ui.jsx";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StepOne({ evaluation, loading, error, onNext }) {
  const requirements = evaluation?.requirements ?? [];
  return (
    <>
      <CornerFrame className="mt-10 flex flex-col gap-3 bg-fg p-6 text-cream">
        <span className="text-eyebrow text-cream/60">
          {loading ? "Loading…" : `Default checklist · ${requirements.length} requirements`}
        </span>
        <span className="text-pullquote" style={{ fontSize: 22 }}>
          BPP / PPA 2007 Standard Checklist
        </span>
        <span className="text-caption text-cream/65">
          The 10-requirement default technical-compliance checklist (CAC, Tax Clearance, PENCOM,
          ITF, NSITF, Audited Accounts, Professional Registration, Key Personnel CVs, Similar
          Project Experience, Equipment Schedule).
        </span>
      </CornerFrame>

      {error && (
        <p className="text-caption mt-4 text-[#96291c]">
          Couldn't reach the backend ({error}). Is it running at{" "}
          <code>uvicorn app.main:app --reload</code>?
        </p>
      )}

      {requirements.length > 0 && (
        <div className="mt-10">
          <h2 className="text-eyebrow text-fg/55">Requirements that will be checked</h2>
          <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
            {requirements.map((r, i) => (
              <li
                key={r.id}
                className="flex items-baseline gap-4 border-b border-dashed border-fg/12 px-5 py-3 last:border-0"
              >
                <span className="text-eyebrow shrink-0 text-fg/40">{String(i + 1).padStart(2, "0")}</span>
                <span className="text-caption text-fg">{r.name}</span>
                {r.is_mandatory && <span className="text-eyebrow ml-auto shrink-0 text-fg/40">Mandatory</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-10 flex justify-end">
        <PrimaryButton onClick={onNext} className={!evaluation ? "pointer-events-none opacity-40" : ""}>
          <span className="inline-flex items-center gap-2">
            Next: Contractor Submission <ArrowRight size={15} />
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
  const [evaluation, setEvaluation] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [files, setFiles] = useState([]);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    createDefaultEvaluation()
      .then((ev) => {
        if (!cancelled) setEvaluation(ev);
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
        <StepOne evaluation={evaluation} loading={loading} error={loadError} onNext={() => setStep(2)} />
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
