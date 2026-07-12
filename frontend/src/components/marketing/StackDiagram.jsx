import { CornerFrame } from "../ui.jsx";

const LAYERS = [
  {
    id: "officer",
    title: "Procurement Officer",
    body: "Sets the tender, reviews flags, and approves the final decision.",
  },
  {
    id: "agent",
    title: "Cribra Agent",
    body: "RAG + GPT-4o evaluation of every requirement, with justifications.",
  },
  {
    id: "knowledge",
    title: "Statutory Knowledge Base",
    body: "PPA 2007 and the BPP Standard Bidding Documents, indexed for retrieval.",
  },
  {
    id: "submission",
    title: "Contractor Submission",
    body: "Certificates, accounts, schedules, CVs — the documents under evaluation.",
  },
];

/**
 * The layered stack diagram from Antimetal's "Where we sit" section,
 * adapted to Cribra: officer → agent → knowledge base → submission.
 * `active` (0–2) highlights layers as the sticky cards scroll.
 */
export default function StackDiagram({ active = 0 }) {
  const emphasis = {
    0: ["officer"],
    1: ["agent", "knowledge"],
    2: ["officer", "agent"],
  }[active] ?? [];

  return (
    <div className="relative mx-auto flex w-full max-w-[640px] flex-col gap-4">
      {LAYERS.map((layer, i) => {
        const on = emphasis.includes(layer.id);
        return (
          <div
            key={layer.id}
            className="transition-all duration-700"
            style={{
              transform: `translateX(${i * 14}px) ${on ? "scale(1.015)" : "scale(1)"}`,
              opacity: on ? 1 : 0.55,
              transitionTimingFunction: "cubic-bezier(0.22,1,0.36,1)",
            }}
          >
            <CornerFrame className={`p-6 md:p-7 ${on ? "bg-cream/60" : ""}`}>
              <h3 className="text-pullquote text-fg" style={{ fontSize: "clamp(20px,1.8vw,28px)" }}>
                {layer.title}
              </h3>
              <p className="mt-1 text-caption text-fg/60">{layer.body}</p>
            </CornerFrame>
            {i < LAYERS.length - 1 && (
              <div className="flex justify-center py-1" aria-hidden="true">
                <svg width="10" height="18" viewBox="0 0 10 18" fill="none">
                  <path d="M5 0 V14 M1 10 L5 14 L9 10" stroke="rgba(26,23,20,0.4)" strokeWidth="1.2" />
                </svg>
              </div>
            )}
          </div>
        );
      })}
      {/* sieve glyph beside the stack */}
      <div className="pointer-events-none absolute -right-2 top-1/2 hidden -translate-y-1/2 xl:block" aria-hidden="true">
        <img src="/cribra-mark.svg" alt="" className="w-[72px] opacity-70" />
      </div>
    </div>
  );
}
