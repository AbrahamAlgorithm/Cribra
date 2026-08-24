import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ChevronDown, Download, ArrowLeft, Loader2 } from "lucide-react";
import { getReport } from "../lib/api.js";
import { StatusBadge, ScoreRing } from "../components/app.jsx";
import { CornerFrame, Reveal } from "../components/ui.jsx";

function Row({ result }) {
  const [open, setOpen] = useState(false);
  const source = result.requirement_source;
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        className="cursor-pointer border-b border-dashed border-fg/12 transition-colors hover:bg-cream"
      >
        <td className="text-caption px-4 py-4 font-medium text-fg">{result.requirement_name}</td>
        <td className="px-4 py-4">
          <StatusBadge status={result.status} />
        </td>
        <td className="text-caption px-4 py-4 text-fg/60 max-lg:hidden" style={{ fontSize: 13 }}>
          {result.evidence_found}
        </td>
        <td className="px-4 py-4 text-right">
          <ChevronDown
            size={15}
            className="inline text-fg/40 transition-transform duration-300"
            style={{ transform: open ? "rotate(180deg)" : "none" }}
          />
        </td>
      </tr>
      {open && (
        <tr className="border-b border-dashed border-fg/12 bg-cream/70">
          <td />
          <td colSpan={3} className="px-4 py-5">
            <div className="grid max-w-[860px] grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <div className="text-eyebrow text-fg/50">Justification</div>
                <p className="text-caption mt-2 text-fg/80">{result.justification}</p>
                {result.confidence_note && (
                  <p className="text-caption mt-2 text-fg/50" style={{ fontSize: 12.5 }}>
                    {result.confidence_note}
                  </p>
                )}
              </div>
              <div>
                <div className="text-eyebrow text-fg/50">Source</div>
                <p className="text-caption mt-2 text-fg/70">
                  {source?.document_name || "—"}
                  {source?.section_reference ? ` · ${source.section_reference}` : ""}
                </p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function Report() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [issuesOnly, setIssuesOnly] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getReport(id)
      .then((r) => {
        if (!cancelled) setReport(r);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const rows = useMemo(() => {
    if (!report) return [];
    return issuesOnly ? report.results.filter((r) => r.status !== "Compliant") : report.results;
  }, [issuesOnly, report]);

  if (error) {
    return (
      <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
        <p className="text-caption text-[#96291c]">Couldn't load this report: {error}</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 size={20} className="animate-spin text-fg/40" />
      </div>
    );
  }

  const { summary } = report;

  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <Link
          to="/app"
          className="text-button inline-flex items-center gap-2 text-fg/55 transition-colors hover:text-fg"
        >
          <ArrowLeft size={14} /> Dashboard
        </Link>

        <CornerFrame className="mt-6 bg-cream/70 p-8">
          <div className="flex flex-wrap items-center justify-between gap-8">
            <div className="min-w-0">
              <p className="text-eyebrow text-fg/50">
                Compliance report · {report.evaluation_id} · {new Date(report.generated_at).toLocaleString()}
              </p>
              <h1 className="text-subhead mt-3 text-fg" style={{ fontSize: "clamp(26px,2.8vw,40px)" }}>
                Technical Compliance Evaluation
              </h1>
              <p className="text-caption mt-2 text-fg/60">
                {summary.requirements_evaluated} requirements checked against the default BPP/PPA checklist
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <StatusBadge status="Compliant" />
                <span className="text-caption -ml-1 mr-3 self-center text-fg/60">{summary.compliant}</span>
                <StatusBadge status="Non-Compliant" />
                <span className="text-caption -ml-1 mr-3 self-center text-fg/60">{summary.non_compliant}</span>
                <StatusBadge status="Needs Review" />
                <span className="text-caption -ml-1 self-center text-fg/60">{summary.needs_review}</span>
              </div>
            </div>
            <ScoreRing score={Math.round(summary.compliance_score)} />
          </div>
        </CornerFrame>
      </Reveal>

      <Reveal delay={60}>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          <CornerFrame className="p-6">
            <div className="text-eyebrow text-fg/50">Overall assessment</div>
            <p className="text-caption mt-3 text-fg/80">{report.overall_assessment}</p>
          </CornerFrame>
          <CornerFrame className="p-6">
            <div className="text-eyebrow text-fg/50">Observations</div>
            <ul className="mt-3 flex flex-col gap-2">
              {report.observations.map((o, i) => (
                <li key={i} className="text-caption text-fg/80">
                  · {o}
                </li>
              ))}
            </ul>
          </CornerFrame>
        </div>
      </Reveal>

      <Reveal delay={100}>
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
          <label className="flex cursor-pointer items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={issuesOnly}
              onClick={() => setIssuesOnly(!issuesOnly)}
              className={`relative h-[22px] w-[40px] rounded-full transition-colors ${
                issuesOnly ? "bg-fg" : "bg-fg/20"
              }`}
            >
              <span
                className="absolute top-[3px] h-4 w-4 rounded-full bg-cream transition-all"
                style={{ left: issuesOnly ? 20 : 3 }}
              />
            </button>
            <span className="text-button text-fg/70">Issues only</span>
          </label>
          <button
            type="button"
            onClick={() => window.print()}
            className="text-button inline-flex items-center gap-2 rounded-full bg-fg px-5 py-[10px] text-cream transition-colors hover:bg-fg/85"
          >
            <Download size={14} /> Export to PDF
          </button>
        </div>

        <div className="mt-4 overflow-x-auto border border-dashed border-[var(--color-border)] bg-cream/50">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead>
              <tr className="border-b border-fg/15">
                <th className="text-eyebrow px-4 py-3 font-medium text-fg/45">Requirement</th>
                <th className="text-eyebrow px-4 py-3 font-medium text-fg/45">Status</th>
                <th className="text-eyebrow px-4 py-3 font-medium text-fg/45 max-lg:hidden">
                  Evidence found
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <Row key={r.requirement_id} result={r} />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-caption mt-4 text-fg/45" style={{ fontSize: 12.5 }}>
          Cribra is decision support. Findings are AI-generated from the submitted documents and the
          statutory sources; the evaluation committee reviews all flags and the procurement officer
          makes the final determination.
        </p>
      </Reveal>
    </div>
  );
}
