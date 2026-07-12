import { Link } from "react-router-dom";
import { CornerFrame, CribraMark } from "../components/ui.jsx";

export function Field({ label, type = "text", placeholder, value, onChange, options }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-eyebrow text-fg/55">{label}</span>
      {options ? (
        <select
          value={value}
          onChange={onChange}
          className="w-full rounded-none border border-dashed border-[var(--color-border)] bg-cream/60 px-4 py-3 text-caption text-fg outline-none focus:border-fg/60"
        >
          {options.map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          className="w-full rounded-none border border-dashed border-[var(--color-border)] bg-cream/60 px-4 py-3 text-caption text-fg outline-none placeholder:text-fg/35 focus:border-fg/60"
        />
      )}
    </label>
  );
}

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden px-4 py-16">
      <div className="relative z-10 w-full max-w-[460px]">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <CribraMark className="h-5 w-auto" />
          <span className="text-fg" style={{ fontFamily: "var(--font-sans)", fontWeight: 500, fontSize: 18 }}>
            Cribra
          </span>
        </Link>
        <CornerFrame className="bg-cream/80 p-8 backdrop-blur-sm md:p-10">
          <h1 className="text-subhead text-fg" style={{ fontSize: "clamp(26px,2.6vw,36px)" }}>
            {title}
          </h1>
          <p className="text-caption mt-2 text-fg/60">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </CornerFrame>
        <div className="text-caption mt-6 text-center text-fg/60">{footer}</div>
      </div>
    </main>
  );
}
