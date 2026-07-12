import { Link } from "react-router-dom";
import { ArrowRight, Plus } from "lucide-react";
import data from "../data/mockData.json";
import { StatTile } from "../components/app.jsx";
import { PrimaryButton, Reveal } from "../components/ui.jsx";

export default function Dashboard() {
  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-eyebrow text-fg/50">Workspace</p>
            <h1 className="text-subhead mt-2 text-fg" style={{ fontSize: "clamp(28px,3vw,42px)" }}>
              Good day, {data.user.name.split(" ")[0]}.
            </h1>
          </div>
          <PrimaryButton to="/app/evaluations/new">
            <span className="inline-flex items-center gap-2">
              <Plus size={15} /> New Evaluation
            </span>
          </PrimaryButton>
        </div>
      </Reveal>

      <Reveal delay={80}>
        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatTile label="Evaluations run" value={data.stats.evaluationsRun} hint="All time" />
          <StatTile
            label="Avg. compliance rate"
            value={`${data.stats.avgComplianceRate}%`}
            hint="Across completed evaluations"
          />
          <StatTile
            label="Submissions flagged"
            value={data.stats.flaggedSubmissions}
            hint="Contained Missing or Needs Review items"
          />
        </div>
      </Reveal>

      <Reveal delay={160}>
        <div className="mt-12">
          <div className="flex items-center justify-between">
            <h2 className="text-eyebrow text-fg/55">Recent evaluations</h2>
            <Link to="/app/evaluations" className="text-button flex items-center gap-1 text-fg/60 hover:text-fg">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <ul className="mt-4 border border-dashed border-[var(--color-border)] bg-cream/60">
            {data.evaluations.slice(0, 4).map((ev) => (
              <li key={ev.id} className="border-b border-dashed border-fg/12 last:border-0">
                <Link
                  to={`/app/evaluations/${ev.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-cream"
                >
                  <div className="min-w-0">
                    <div className="text-button truncate text-fg">{ev.contractor}</div>
                    <div className="text-caption truncate text-fg/50" style={{ fontSize: 13 }}>
                      {ev.project}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-6">
                    <span className="text-eyebrow text-fg/45">{ev.date}</span>
                    <span
                      className="font-serif text-[22px]"
                      style={{
                        color: ev.score >= 80 ? "#1b7a43" : ev.score >= 60 ? "#b7791f" : "#c03a2b",
                      }}
                    >
                      {ev.score}%
                    </span>
                    <ArrowRight size={15} className="text-fg/35" />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </Reveal>
    </div>
  );
}
