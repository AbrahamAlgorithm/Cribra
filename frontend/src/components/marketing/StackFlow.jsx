import { CornerFrame, CribraMark } from "../ui.jsx";

/**
 * The animated stack diagram for the "How it works" sticky-scroll section.
 * Choreography mirrors Antimetal's:
 *   - starts FLAT, facing the viewer, with just Officer + Submission
 *   - tilts into a 3D isometric plane as the Cribra layers build in
 *   - tilts back FLAT at the end, showing the complete stack face-on
 * The tilt is scrubbed directly by scroll progress; stage changes drive the
 * eased build-up tweens. Layers sit with plain gaps — no connector arrows.
 */
const EASE = "cubic-bezier(0.22, 1, 0.36, 1)";

const smoothstep = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/* technical-drawing extension lines; only visible while the plane is tilted */
function ExtLines({ opacity = 0, verticals = false }) {
  const h = "pointer-events-none absolute border-t border-dashed border-fg/20";
  const v = "pointer-events-none absolute border-l border-dashed border-fg/15";
  return (
    <span aria-hidden="true" className="pointer-events-none absolute inset-0" style={{ opacity }}>
      <span className={h} style={{ top: -1, left: -130, width: 120 }} />
      <span className={h} style={{ top: -1, right: -130, width: 120 }} />
      <span className={h} style={{ bottom: -1, left: -90, width: 80 }} />
      <span className={h} style={{ bottom: -1, right: -90, width: 80 }} />
      {verticals && (
        <>
          <span className={v} style={{ left: -1, top: -90, height: 80 }} />
          <span className={v} style={{ right: -1, bottom: -90, height: 80 }} />
        </>
      )}
    </span>
  );
}

/* collapsible row: grid-rows 0fr -> 1fr with eased stagger, like a tween */
function Expand({ open, delay = 0, children }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateRows: open ? "1fr" : "0fr",
        transition: `grid-template-rows 850ms ${EASE} ${open ? delay : 0}ms`,
      }}
    >
      <div style={{ overflow: "hidden" }}>
        <div
          style={{
            opacity: open ? 1 : 0,
            transform: open ? "translateY(0)" : "translateY(16px)",
            transition: `opacity 650ms ${EASE} ${open ? delay + 140 : 0}ms, transform 650ms ${EASE} ${open ? delay + 140 : 0}ms`,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

/* Antimetal-proportioned layer: roomy box, title + body in the upper area,
   open space beneath */
function LayerCard({ title, body, dark = false, chip = null }) {
  return (
    <CornerFrame
      className={`flex min-h-[122px] flex-col justify-center px-6 py-5 transition-colors duration-500 ${dark ? "bg-fg" : "bg-cream/50"}`}
    >
      <div className="flex items-start justify-between gap-4">
        <h3
          className={`font-serif transition-colors duration-500 ${dark ? "text-cream" : "text-fg"}`}
          style={{ fontSize: 14, fontWeight: 500, lineHeight: 1.2 }}
        >
          {title}
        </h3>
        <span
          className="text-eyebrow whitespace-nowrap bg-[#1b7a43] px-2 py-[3px] text-cream"
          style={{
            fontSize: 9,
            opacity: chip ? 1 : 0,
            transform: chip ? "translateY(0)" : "translateY(-6px)",
            transition: `opacity 500ms ${EASE} 250ms, transform 500ms ${EASE} 250ms`,
          }}
        >
          {chip || "FINAL APPROVAL"}
        </span>
      </div>
      <p
        className={`mt-1 transition-colors duration-500 ${dark ? "text-cream/60" : "text-fg/55"}`}
        style={{ fontSize: 11, lineHeight: 1.4, fontFamily: "var(--font-sans)" }}
      >
        {body}
      </p>
    </CornerFrame>
  );
}

const SOURCES = ["PPA 2007", "BPP SBD · WORKS", "Tender Addenda"];

/* cream rendering of the sieve mark for the dark glyph block */
function LightMark({ className = "" }) {
  return (
    <svg viewBox="0 0 40 32" className={className} aria-hidden="true">
      <circle cx="6" cy="5" r="3" fill="#f2efe7" />
      <circle cx="16" cy="5" r="3" fill="#f2efe7" />
      <circle cx="26" cy="5" r="3" fill="#f2efe7" />
      <circle cx="36" cy="5" r="3" fill="#f2efe7" />
      <circle cx="11" cy="14" r="2.6" fill="#f2efe7" />
      <circle cx="21" cy="14" r="2.6" fill="#f2efe7" />
      <circle cx="31" cy="14" r="2.6" fill="#f2efe7" />
      <circle cx="16" cy="22" r="2.2" fill="#5fbf7f" />
      <circle cx="26" cy="22" r="2.2" fill="#5fbf7f" />
      <circle cx="21" cy="29" r="1.8" fill="#5fbf7f" />
    </svg>
  );
}

/* single-line mobile card: short copy + nowrap, with a fluid body size that
   shrinks just enough on narrow phones so text never wraps to two lines */
function MobileLayerCard({ title, body, dark = false, chip = null }) {
  return (
    <CornerFrame
      className={`flex min-h-[74px] flex-col justify-center px-5 py-3 ${dark ? "bg-fg" : "bg-cream/50"}`}
    >
      <div className="flex items-center justify-between gap-3">
        <h3
          className={`whitespace-nowrap font-serif ${dark ? "text-cream" : "text-fg"}`}
          style={{ fontSize: "min(17px, calc((100vw - 88px) / 15))", fontWeight: 500, lineHeight: 1.2 }}
        >
          {title}
        </h3>
        {chip && (
          <span
            className="text-eyebrow whitespace-nowrap bg-[#1b7a43] px-1.5 py-[3px] text-cream"
            style={{ fontSize: 8 }}
          >
            {chip}
          </span>
        )}
      </div>
      <p
        className={`mt-1 whitespace-nowrap ${dark ? "text-cream/60" : "text-fg/55"}`}
        style={{
          fontSize: "min(11px, calc((100vw - 88px) / 23))",
          lineHeight: 1.4,
          fontFamily: "var(--font-sans)",
        }}
      >
        {body}
      </p>
    </CornerFrame>
  );
}

/* mobile arrangement: every layer full-width on top of each other, the glyph
   as its own dark full-width block; only the sources share a row */
function StackedMobile({ stage }) {
  return (
    <div className="flex flex-col gap-3">
      <MobileLayerCard
        dark={stage >= 2}
        chip={stage >= 2 ? "FINAL APPROVAL" : null}
        title="Procurement Officer"
        body="Reviews findings and gives final approval."
      />
      <MobileLayerCard
        title="Cribra Agent"
        body="Evaluates every requirement with evidence."
      />
      <MobileLayerCard
        title="Statutory Knowledge Base"
        body="Nigeria's procurement rules, indexed."
      />
      <div className="flex min-h-[130px] items-center justify-center bg-fg">
        <LightMark className="w-[72px]" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {SOURCES.map((s) => (
          <CornerFrame key={s} className="flex min-h-[48px] items-center justify-center bg-cream/50 px-1">
            <span className="text-eyebrow whitespace-nowrap text-fg/60" style={{ fontSize: 8 }}>
              {s}
            </span>
          </CornerFrame>
        ))}
      </div>
      <MobileLayerCard
        title="Contractor Submission"
        body="The contractor's documents under review."
      />
    </div>
  );
}

function Stack({ stage, lines }) {
  return (
    <>
      <div className="relative">
        <ExtLines opacity={lines} verticals />
        <LayerCard
          dark={stage >= 2}
          chip={stage >= 2 ? "FINAL APPROVAL" : null}
          title="Procurement Officer"
          body="Oversees the evaluation and approves the final determination."
        />
      </div>

      {/* The Cribra middle layer expands in at stage 1 */}
      <Expand open={stage >= 1}>
        <div className="relative grid grid-cols-[minmax(0,1fr)_136px] items-stretch gap-3 pt-3">
          <ExtLines opacity={lines} />
          <div className="flex flex-col gap-3">
            <LayerCard
              title="Cribra Agent"
              body="Evaluates every requirement and produces explainable findings."
            />
            <LayerCard
              title="Statutory Knowledge Base"
              body="Grounded in Nigeria's procurement rules and tender requirements."
            />
          </div>
          <CornerFrame className="flex items-center justify-center bg-cream/50">
            <CribraMark className="w-[56px] opacity-85" />
          </CornerFrame>
        </div>
      </Expand>

      {/* Statutory sources row lands at stage 2 */}
      <Expand open={stage >= 2} delay={120}>
        <div className="relative grid grid-cols-3 gap-3 pt-3">
          {SOURCES.map((s) => (
            <CornerFrame key={s} className="flex min-h-[68px] items-center justify-center bg-cream/50 px-2">
              <span className="text-eyebrow whitespace-nowrap text-fg/60" style={{ fontSize: 8 }}>
                {s}
              </span>
            </CornerFrame>
          ))}
        </div>
      </Expand>

      <div className="relative mt-3">
        <ExtLines opacity={lines} verticals />
        <LayerCard
          title="Contractor Submission"
          body="Contractor evidence submitted for technical compliance evaluation."
        />
      </div>
    </>
  );
}

export default function StackFlow({ stage = 0, progress = 0.5, tilt = true }) {
  if (!tilt) {
    return (
      <div className="relative mx-auto w-full max-w-[560px]">
        <StackedMobile stage={stage} />
      </div>
    );
  }

  // flat -> 3D -> flat: tilt ramps in as the build-up starts and back out
  // before the section ends, so the finished stack faces the viewer
  const t = Math.min(smoothstep(0.1, 0.3, progress), 1 - smoothstep(0.7, 0.9, progress));
  const rx = 44 * t;
  const rz = -12 * t;
  const scale = 1 + 0.06 * t;

  return (
    <div
      className="relative w-full"
      style={{ perspective: "1500px", perspectiveOrigin: "60% 38%" }}
      aria-label="Cribra architecture: procurement officer, Cribra agent over a statutory knowledge base, and the contractor submission"
    >
      <div
        className="mx-auto w-full max-w-[560px]"
        style={{
          transform: `rotateX(${rx}deg) rotateZ(${rz}deg) scale(${scale})`,
          transformStyle: "preserve-3d",
        }}
      >
        <Stack stage={stage} lines={t} />
      </div>
    </div>
  );
}
