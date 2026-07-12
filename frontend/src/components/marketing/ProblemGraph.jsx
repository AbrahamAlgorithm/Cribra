import { useEffect, useRef, useState } from "react";

/**
 * Antimetal-style "representational gap" chart, adapted to Cribra:
 * documents to verify grows exponentially; what an evaluator can check
 * consistently grows linearly. Curves draw on when scrolled into view.
 */
export default function ProblemGraph() {
  const ref = useRef(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setRunning(true);
          io.disconnect();
        }
      },
      { threshold: 0.35 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // exponential + linear paths in a 680x560 viewBox, axes at x=129 / y=520
  const exp = [];
  const lin = [];
  for (let i = 0; i <= 72; i++) {
    const x = 130 + (i / 72) * 536;
    const t = i / 72;
    exp.push(`${i === 0 ? "M" : "L"}${x.toFixed(1)} ${(501 - 444 * (Math.pow(2.9, t * 2.6) - 1) / (Math.pow(2.9, 2.6) - 1)).toFixed(1)}`);
    lin.push(`${i === 0 ? "M" : "L"}${x.toFixed(1)} ${(501 - 58 * t).toFixed(1)}`);
  }

  const ticksX = Array.from({ length: 20 }, (_, i) => 156 + i * 27.35);
  const ticksY = Array.from({ length: 20 }, (_, i) => 494.3 - i * 25.7);

  return (
    <div ref={ref} className={`graph relative ${running ? "is-running" : ""}`}>
      <svg
        viewBox="0 0 680 560"
        role="img"
        aria-label="Chart: the volume of documents and clauses a committee must verify per tender climbs steeply over time, while what an evaluator can check consistently rises only gently. The widening difference is the compliance gap."
        className="h-auto w-full"
      >
        <line className="graph-axis" x1="129" y1="6" x2="129" y2="520" />
        <line className="graph-axis" x1="129" y1="520" x2="676" y2="520" />
        <g>
          {ticksX.map((x, i) => (
            <line key={`x${i}`} className="graph-tick" x1={x} y1="524" x2={x} y2={i % 5 === 4 ? 532 : 528} />
          ))}
          {ticksY.map((y, i) => (
            <line key={`y${i}`} className="graph-tick" x1={i % 5 === 4 ? 117 : 121} y1={y} x2="125" y2={y} />
          ))}
        </g>
        <path className="graph-curve graph-curve--green" d={lin.join("")} />
        <path className="graph-curve graph-curve--red" d={exp.join("")} />
        <circle className="graph-fade" cx="666" cy="443" r="4.6" fill="#6d7a2c" />
        <circle className="graph-fade" cx="666" cy="57" r="4.6" fill="#c05b2e" />
        <g className="graph-fade" stroke="#1a1714" strokeWidth="1.4" fill="none">
          <line x1="666" y1="75" x2="666" y2="425" />
          <path d="M661.9 79.1 L666 75 L670.1 79.1" />
          <path d="M661.9 420.9 L666 425 L670.1 420.9" />
        </g>
      </svg>

      <div aria-hidden="true">
        <span
          className="graph-fade text-eyebrow absolute bg-cream px-2 py-1 text-right text-[#c05b2e]"
          style={{ right: "0%", top: "4.5%" }}
        >
          Documents &amp; clauses
          <br />
          to verify per tender
        </span>
        <span
          className="graph-fade text-eyebrow absolute bg-cream px-2 py-1 text-right text-[#6d7a2c]"
          style={{ right: "0%", top: "78%" }}
        >
          What one evaluator can
          <br />
          check consistently
        </span>
        <span
          className="graph-fade text-eyebrow absolute bg-fg px-2 py-1 text-cream"
          style={{ right: "6%", top: "43%" }}
        >
          The compliance gap
        </span>
        <span
          className="text-eyebrow absolute text-fg/50"
          style={{ left: "8%", top: "50%", transform: "translate(-50%,-50%) rotate(-90deg)" }}
        >
          Workload
        </span>
        <span className="text-eyebrow absolute text-fg/50" style={{ left: "20%", bottom: "-2%" }}>
          Time
        </span>
      </div>
    </div>
  );
}
