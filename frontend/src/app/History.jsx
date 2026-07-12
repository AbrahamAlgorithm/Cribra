import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, ArrowUpDown, ArrowRight } from "lucide-react";
import data from "../data/mockData.json";
import { Reveal } from "../components/ui.jsx";

export default function History() {
  const [query, setQuery] = useState("");
  const [sortDesc, setSortDesc] = useState(true);

  const rows = useMemo(() => {
    const q = query.toLowerCase();
    return data.evaluations
      .filter(
        (e) =>
          e.contractor.toLowerCase().includes(q) ||
          e.project.toLowerCase().includes(q) ||
          e.id.toLowerCase().includes(q)
      )
      .sort((a, b) => (sortDesc ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date)));
  }, [query, sortDesc]);

  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <p className="text-eyebrow text-fg/50">Evaluations</p>
        <h1 className="text-subhead mt-2 text-fg" style={{ fontSize: "clamp(28px,3vw,42px)" }}>
          History
        </h1>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-fg/35" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search contractor, project, or reference…"
              className="w-full border border-dashed border-[var(--color-border)] bg-cream/60 py-3 pl-11 pr-4 text-caption text-fg outline-none placeholder:text-fg/35 focus:border-fg/60"
            />
          </div>
          <button
            type="button"
            onClick={() => setSortDesc(!sortDesc)}
            className="text-button inline-flex items-center gap-2 border border-dashed border-[var(--color-border)] px-4 py-3 text-fg/60 transition-colors hover:text-fg"
          >
            <ArrowUpDown size={14} /> Date {sortDesc ? "↓" : "↑"}
          </button>
        </div>

        <div className="mt-6 overflow-x-auto border border-dashed border-[var(--color-border)] bg-cream/50">
          <table className="w-full min-w-[680px] border-collapse text-left">
            <thead>
              <tr className="border-b border-fg/15">
                {["Reference", "Contractor", "Requirement set", "Date", "Score", ""].map((h) => (
                  <th key={h} className="text-eyebrow px-4 py-3 font-medium text-fg/45">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((ev) => (
                <tr key={ev.id} className="border-b border-dashed border-fg/12 transition-colors last:border-0 hover:bg-cream">
                  <td className="text-eyebrow px-4 py-4 text-fg/50">{ev.id}</td>
                  <td className="px-4 py-4">
                    <Link to={`/app/evaluations/${ev.id}`} className="text-caption font-medium text-fg hover:underline">
                      {ev.contractor}
                    </Link>
                    <div className="text-caption text-fg/45" style={{ fontSize: 12.5 }}>
                      {ev.project}
                    </div>
                  </td>
                  <td className="text-caption px-4 py-4 text-fg/60">{ev.requirementSet}</td>
                  <td className="text-eyebrow px-4 py-4 text-fg/50">{ev.date}</td>
                  <td className="px-4 py-4">
                    <span
                      className="font-serif text-[20px]"
                      style={{
                        color: ev.score >= 80 ? "#1b7a43" : ev.score >= 60 ? "#b7791f" : "#c03a2b",
                      }}
                    >
                      {ev.score}%
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <Link to={`/app/evaluations/${ev.id}`} aria-label={`Open ${ev.id}`}>
                      <ArrowRight size={15} className="inline text-fg/35" />
                    </Link>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-caption px-4 py-10 text-center text-fg/45">
                    No evaluations match “{query}”.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Reveal>
    </div>
  );
}
