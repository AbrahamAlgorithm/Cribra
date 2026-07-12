import { BookOpenText, ScrollText } from "lucide-react";
import data from "../data/mockData.json";
import { CornerFrame, Reveal } from "../components/ui.jsx";

const SOURCES = [
  {
    icon: ScrollText,
    title: "Public Procurement Act, 2007",
    detail: "Act No. 14 of 2007 · Sections 16 & 24–38 indexed",
    chunks: "412 indexed passages",
  },
  {
    icon: BookOpenText,
    title: "BPP Standard Bidding Document (Works)",
    detail: "2011 edition · Sections I–IV indexed",
    chunks: "268 indexed passages",
  },
];

export default function KnowledgeBase() {
  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <p className="text-eyebrow text-fg/50">Knowledge base</p>
        <h1 className="text-subhead mt-2 text-fg" style={{ fontSize: "clamp(28px,3vw,42px)" }}>
          Statutory sources &amp; requirement sets
        </h1>
        <p className="text-caption mt-3 max-w-[64ch] text-fg/60">
          Read-only view of the sources the agent retrieves from, and the requirement sets built on
          them.
        </p>

        <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
          {SOURCES.map((s) => (
            <CornerFrame key={s.title} className="flex flex-col gap-3 bg-cream/60 p-6">
              <s.icon size={20} className="text-fg/45" />
              <div className="text-pullquote text-fg" style={{ fontSize: 22 }}>
                {s.title}
              </div>
              <div className="text-caption text-fg/55">{s.detail}</div>
              <div className="text-eyebrow mt-2 self-start border border-fg/15 bg-fg/5 px-2 py-1 text-fg/50">
                {s.chunks}
              </div>
            </CornerFrame>
          ))}
        </div>

        <h2 className="text-eyebrow mt-12 text-fg/55">Requirement sets</h2>
        <div className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
          {data.requirementSets.map((set) => (
            <div key={set.id} className="border-b border-dashed border-fg/12 px-5 py-4 last:border-0">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-button text-fg">{set.name}</span>
                <span className="text-eyebrow text-fg/45">{set.count} requirements · {set.source}</span>
              </div>
              <p className="text-caption mt-1 text-fg/55">{set.description}</p>
            </div>
          ))}
        </div>

        <h2 className="text-eyebrow mt-12 text-fg/55">All requirements — BPP Works, Standard</h2>
        <ul className="mt-3 border border-dashed border-[var(--color-border)] bg-cream/60">
          {data.requirements.map((r) => (
            <li key={r.id} className="border-b border-dashed border-fg/12 px-5 py-4 last:border-0">
              <div className="flex items-baseline gap-4">
                <span className="text-eyebrow shrink-0 text-fg/40">{r.id}</span>
                <div>
                  <div className="text-caption font-medium text-fg">{r.title}</div>
                  <p className="text-caption mt-1 text-fg/55" style={{ fontSize: 13 }}>
                    {r.text}
                  </p>
                  <span className="text-eyebrow mt-2 inline-block text-fg/40">{r.ref}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </Reveal>
    </div>
  );
}
