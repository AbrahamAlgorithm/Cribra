import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

/* Corner bracket used on Antimetal-style dashed frames */
function Corner({ pos }) {
  const paths = {
    tl: "M 1.25 10 L 1.25 1.25 L 10 1.25",
    tr: "M 0 1.25 L 8.75 1.25 L 8.75 10",
    bl: "M 1.25 0 L 1.25 8.75 L 10 8.75",
    br: "M 0 8.75 L 8.75 8.75 L 8.75 0",
  };
  const style = {
    tl: { top: -1, left: -1 },
    tr: { top: -1, right: -1 },
    bl: { bottom: -1, left: -1 },
    br: { bottom: -1, right: -1 },
  };
  return (
    <span
      aria-hidden="true"
      className="pointer-events-none absolute leading-none"
      style={style[pos]}
    >
      <svg width="7" height="7" viewBox="0 0 10 10" fill="none" overflow="visible">
        <path d={paths[pos]} stroke="currentColor" strokeWidth="1.5" fill="none" />
      </svg>
    </span>
  );
}

export function CornerFrame({ as: Tag = "div", className = "", children, ...rest }) {
  return (
    <Tag className={`relative border border-dashed border-[var(--color-border)] ${className}`} {...rest}>
      {children}
      <Corner pos="tl" />
      <Corner pos="tr" />
      <Corner pos="bl" />
      <Corner pos="br" />
    </Tag>
  );
}

/* IntersectionObserver-driven fade/slide-up, like Antimetal's section reveals */
export function Reveal({ children, delay = 0, className = "" }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div
      ref={ref}
      className={`reveal ${visible ? "is-visible" : ""} ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

/* "01 · SECTION NAME" header row */
export function SectionEyebrow({ number, label }) {
  return (
    <div className="flex items-center gap-8">
      <span className="text-eyebrow text-fg/60">{number}</span>
      <span aria-hidden="true" className="h-[2px] w-[2px] shrink-0 rounded-full bg-fg/20" />
      <span className="text-eyebrow text-fg/60">{label}</span>
    </div>
  );
}

export function PrimaryButton({ to, onClick, children, className = "", type }) {
  const cls = `inline-flex cursor-pointer items-center justify-center whitespace-nowrap rounded-full bg-fg px-[24.5px] py-[12.5px] text-button text-cream transition-colors duration-200 hover:bg-fg/85 ${className}`;
  if (to) {
    return (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type={type || "button"} onClick={onClick} className={cls}>
      {children}
    </button>
  );
}

export function FrameButton({ to, onClick, children, className = "" }) {
  const inner = (
    <CornerFrame
      className={`inline-flex cursor-pointer items-center justify-center whitespace-nowrap rounded-full px-[24.5px] py-[12.5px] text-button text-fg transition-colors duration-200 hover:bg-white/25 ${className}`}
    >
      {children}
    </CornerFrame>
  );
  if (to) {
    return (
      <Link to={to} className="inline-flex">
        {inner}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className="inline-flex">
      {inner}
    </button>
  );
}

export function CribraMark({ className = "h-4 w-auto" }) {
  return <img src="/cribra-mark.svg" alt="" className={className} />;
}
