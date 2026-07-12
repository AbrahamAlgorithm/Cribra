import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ChevronDown, Download, ArrowLeft } from "lucide-react";
import data from "../data/mockData.json";
import { StatusBadge, ScoreRing } from "../components/app.jsx";
import { CornerFrame, Reveal } from "../components/ui.jsx";

const reqById = Object.fromEntries(data.requirements.map((r) => [r.id, r]));

function Row({ result }) {
  const [open, setOpen] = useState(false);
  const req = reqById[result.reqId];
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        className="cursor-pointer border-b border-dashed border-fg/12 transition-colors hover:bg-cream"
      >
        <td className="text-eyebrow px-4 py-4 text-fg/40">{result.reqId}</td>
        <td className="text-caption px-4 py-4 font-medium text-fg">{req.title}</td>
        <td className="px-4 py-4">
          <StatusBadge status={result.status} />
        </td>
        <td className="text-caption px-4 py-4 text-fg/60 max-lg:hidden" style={{ fontSize: 13 }}>
          {result.evidence}
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
          <td colSpan={4} className="px-4 py-5">
            <div className="grid max-w-[860px] grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <div className="text-eyebrow text-fg/50">Justification</div>
                <p className="text-caption mt-2 text-fg/80">{result.justification}</p>
              </div>
              <div>
                <div className="text-eyebrow text-fg/50">Requirement checked · {req.ref}</div>
                <p className="text-caption mt-2 text-fg/70">{req.text}</p>
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
  const evaluation = data.evaluations.find((e) => e.id === id) || data.evaluations[0];
  const results = evaluation.results.length ? evaluation.results : data.evaluations[0].results;
  const [issuesOnly, setIssuesOnly] = useState(false);

  const rows = useMemo(
    () => (issuesOnly ? results.filter((r) => r.status !== "Compliant") : results),
    [issuesOnly, results]
  );

  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <Link
          to="/app/evaluations"
          className="text-button inline-flex items-center gap-2 text-fg/55 transition-colors hover:text-fg"
        >
          <ArrowLeft size={14} /> Evaluations
        </Link>

        {/* Report header */}
        <CornerFrame className="mt-6 bg-cream/70 p-8">
          <div className="flex flex-wrap items-center justify-between gap-8">
            <div className="min-w-0">
              <p className="text-eyebrow text-fg/50">
                Compliance report · {evaluation.id} · {evaluation.date}
              </p>
              <h1 className="text-subhead mt-3 text-fg" style={{ fontSize: "clamp(26px,2.8vw,40px)" }}>
                {evaluation.contractor}
              </h1>
              <p className="text-caption mt-2 text-fg/60">
                {evaluation.project} · Checked against {evaluation.requirementSet}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <StatusBadge status="Compliant" />
                <span className="text-caption -ml-1 mr-3 self-center text-fg/60">{evaluation.counts.compliant}</span>
                <StatusBadge status="Missing" />
                <span className="text-caption -ml-1 mr-3 self-center text-fg/60">{evaluation.counts.missing}</span>
                <StatusBadge status="Needs Review" />
                <span className="text-caption -ml-1 self-center text-fg/60">{evaluation.counts.review}</span>
              </div>
            </div>
            <ScoreRing score={evaluation.score} />
          </div>
        </CornerFrame>
      </Reveal>

      <Reveal delay={100}>
        {/* Controls */}
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

        {/* Results table */}
        <div className="mt-4 overflow-x-auto border border-dashed border-[var(--color-border)] bg-cream/50">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead>
              <tr className="border-b border-fg/15">
                <th className="text-eyebrow px-4 py-3 font-medium text-fg/45">#</th>
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
                <Row key={r.reqId} result={r} />
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
