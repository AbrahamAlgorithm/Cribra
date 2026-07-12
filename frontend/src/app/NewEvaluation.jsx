import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, ArrowRight, ArrowLeft, Play } from "lucide-react";
import data from "../data/mockData.json";
import { Stepper, FileListItem } from "../components/app.jsx";
import { CornerFrame, PrimaryButton, FrameButton, Reveal } from "../components/ui.jsx";

function StepOne({ selected, setSelected, onNext }) {
  const previewReqs = data.requirements.slice(0, 6);
  return (
    <>
      <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
        {data.requirementSets.map((set) => (
          <button key={set.id} type="button" onClick={() => setSelected(set.id)} className="text-left">
            <CornerFrame
              className={`flex h-full flex-col gap-3 p-6 transition-colors ${
                selected === set.id ? "bg-fg text-cream" : "bg-cream/60 hover:bg-cream"
              }`}
            >
              <span className={`text-eyebrow ${selected === set.id ? "text-cream/60" : "text-fg/50"}`}>
                Preloaded set · {set.count} requirements
              </span>
              <span className="text-pullquote" style={{ fontSize: 22 }}>
                {set.name}
              </span>
              <span className={`text-caption ${selected === set.id ? "text-cream/65" : "text-fg/55"}`}>
                {set.description}
              </span>
              <span className={`text-eyebrow mt-auto ${selected === set.id ? "text-cream/50" : "text-fg/40"}`}>
                {set.source}
              </span>
            </CornerFrame>
          </button>
        ))}
      </div>

      <CornerFrame className="mt-4 flex items-center justify-between gap-4 p-5">
        <div className="flex items-center gap-3">
          <UploadCloud size={18} className="text-fg/45" />
          <span className="text-caption text-fg/60">
            Or upload a tender document and let Cribra extract the requirements.
          </span>
        </div>
        <span className="text-eyebrow border border-fg/15 bg-fg/5 px-2 py-1 text-fg/45">Prototype</span>
      </CornerFrame>

      <div className="mt-10">
        <h2 className="text-eyebrow text-fg/55">Requirements that will be checked</h2>
        <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
          {previewReqs.map((r) => (
            <li key={r.id} className="flex items-baseline gap-4 border-b border-dashed border-fg/12 px-5 py-3 last:border-0">
              <span className="text-eyebrow shrink-0 text-fg/40">{r.id}</span>
              <span className="text-caption text-fg">{r.title}</span>
              <span className="text-eyebrow ml-auto shrink-0 text-fg/40">{r.ref}</span>
            </li>
          ))}
          <li className="text-caption px-5 py-3 text-fg/45">+ {data.requirements.length - previewReqs.length} more…</li>
        </ul>
      </div>

      <div className="mt-10 flex justify-end">
        <PrimaryButton onClick={onNext}>
          <span className="inline-flex items-center gap-2">
            Next: Contractor Submission <ArrowRight size={15} />
          </span>
        </PrimaryButton>
      </div>
    </>
  );
}

function StepTwo({ files, setFiles, onBack, onRun }) {
  const [staged, setStaged] = useState(files.length > 0);
  return (
    <>
      <CornerFrame className="mt-10 p-2">
        <button
          type="button"
          onClick={() => {
            setStaged(true);
            setFiles(data.uploadFiles);
          }}
          className="flex w-full flex-col items-center justify-center gap-3 border border-dashed border-fg/20 bg-cream/50 px-6 py-14 transition-colors hover:bg-cream"
        >
          <UploadCloud size={28} className="text-fg/40" />
          <span className="text-body text-fg/70" style={{ fontSize: 18 }}>
            Drag &amp; drop the contractor's documents
          </span>
          <span className="text-caption text-fg/45">
            or click to browse — PDF, DOCX, XLSX (prototype: loads a sample submission)
          </span>
        </button>
      </CornerFrame>

      {staged && files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-eyebrow text-fg/55">
            Submission — Zenith Bond Construction Ltd · {files.length} files
          </h2>
          <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
            {files.map((f, i) => (
              <FileListItem
                key={f.name}
                file={f}
                onRemove={() => setFiles(files.filter((_, j) => j !== i))}
              />
            ))}
          </ul>
        </div>
      )}

      <div className="mt-10 flex items-center justify-between">
        <FrameButton onClick={onBack}>
          <span className="inline-flex items-center gap-2">
            <ArrowLeft size={15} /> Back
          </span>
        </FrameButton>
        <PrimaryButton onClick={onRun} className={files.length === 0 ? "pointer-events-none opacity-40" : ""}>
          <span className="inline-flex items-center gap-2">
            <Play size={14} /> Run Evaluation
          </span>
        </PrimaryButton>
      </div>
    </>
  );
}

export default function NewEvaluation() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState(data.requirementSets[0].id);
  const [files, setFiles] = useState([]);

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
        <StepOne selected={selected} setSelected={setSelected} onNext={() => setStep(2)} />
      ) : (
        <StepTwo
          files={files}
          setFiles={setFiles}
          onBack={() => setStep(1)}
          onRun={() => navigate("/app/evaluations/processing")}
        />
      )}
    </div>
  );
}
