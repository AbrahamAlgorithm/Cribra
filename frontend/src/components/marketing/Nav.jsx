import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { CribraMark } from "../ui.jsx";

const links = [
  { label: "The Problem", to: "/#problem" },
  { label: "How it works", to: "/#how-it-works" },
  { label: "What it does", to: "/#capabilities" },
  { label: "Research", to: "/research" },
  { label: "FAQ", to: "/#faq" },
];

const EASE = "cubic-bezier(0.22, 1, 0.36, 1)";

function NavLink({ label, to, onNavigate, className }) {
  if (to.includes("#")) {
    // full path (not stripped) so this also works when navigating in from
    // another page — the browser loads "/" then scrolls to the fragment
    return (
      <a href={to} onClick={onNavigate} className={className}>
        {label}
      </a>
    );
  }
  return (
    <Link to={to} onClick={onNavigate} className={className}>
      {label}
    </Link>
  );
}

export default function Nav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open]);

  const desktopLinkCls =
    "block whitespace-nowrap rounded-full px-3.5 py-2 text-button text-fg/65 transition-colors duration-200 hover:bg-white/40 hover:text-fg";
  const drawerLinkCls =
    "block w-full border-b border-fg/8 py-4 text-[17px] font-medium text-fg/80 transition-colors hover:text-fg";

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 px-4 pt-4 md:px-[30px] md:pt-5">
        <div className="mx-auto grid h-[56px] w-full max-w-[1040px] grid-cols-[1fr_auto] lg:grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-full border border-white/50 bg-white/25 px-3 shadow-[0_8px_30px_rgba(26,23,20,0.10)] backdrop-blur-xl backdrop-saturate-150 sm:h-[62px] sm:gap-4 sm:px-5">
          <Link to="/" aria-label="Cribra home" className="flex items-center gap-2 justify-self-start py-2 sm:gap-2.5">
            <CribraMark className="h-[18px] w-auto sm:h-[19px]" />
            <span
              className="text-fg"
              style={{
                fontFamily: "var(--font-sans)",
                fontWeight: 600,
                fontSize: 19,
                letterSpacing: "-0.02em",
                lineHeight: 1,
              }}
            >
              Cribra
            </span>
          </Link>

          <ul className="hidden items-center justify-center gap-0.5 justify-self-center lg:flex">
            {links.map((l) => (
              <li key={l.label}>
                <NavLink {...l} className={desktopLinkCls} />
              </li>
            ))}
          </ul>

          {/* Sign In / Get Started only appear here at desktop widths — on
              mobile they live inside the slide-in drawer instead */}
          <div className="flex items-center justify-end justify-self-end gap-2">
            <Link
              to="/signin"
              className="hidden whitespace-nowrap rounded-full px-4 py-2 text-button text-fg/65 transition-colors duration-200 hover:bg-white/40 hover:text-fg lg:block"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="hidden whitespace-nowrap rounded-full bg-fg px-5 py-[11px] text-button text-cream transition-colors duration-200 hover:bg-fg/85 lg:block"
            >
              Get Started
            </Link>
            <button
              type="button"
              onClick={() => setOpen(true)}
              aria-controls="mobile-nav-drawer"
              aria-label="Open menu"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-fg/70 transition-colors hover:bg-white/40 hover:text-fg lg:hidden"
            >
              <Menu size={18} />
            </button>
          </div>
        </div>
      </nav>

      {/* Overlay is viewport-sized with clipped overflow, so the drawer can
          sit off-screen at translateX(100%) without extending page width. */}
      <div
        className="fixed inset-0 z-[60] overflow-hidden lg:hidden"
        style={{ pointerEvents: open ? "auto" : "none" }}
      >
        {/* dimmed backdrop behind the drawer */}
        <div
          aria-hidden="true"
          onClick={() => setOpen(false)}
          className="absolute inset-0 bg-fg/35"
          style={{
            opacity: open ? 1 : 0,
            transition: `opacity 400ms ${EASE}`,
          }}
        />

        {/* menu panel — slides in from the right, and back out to the right */}
        <div
          id="mobile-nav-drawer"
          role="dialog"
          aria-modal="true"
          aria-label="Menu"
          aria-hidden={!open}
          className="absolute inset-y-0 right-0 z-[70] flex h-full w-[84vw] max-w-[360px] flex-col bg-[var(--color-bg)] shadow-[-20px_0_60px_rgba(26,23,20,0.18)]"
          style={{
            transform: open ? "translateX(0)" : "translateX(100%)",
            transition: `transform 480ms ${EASE}`,
          }}
        >
        <div className="flex items-center justify-between px-6 pt-6">
          <Link to="/" onClick={() => setOpen(false)} className="flex items-center gap-2.5">
            <CribraMark className="h-[19px] w-auto" />
            <span
              className="text-fg"
              style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 19, letterSpacing: "-0.02em" }}
            >
              Cribra
            </span>
          </Link>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="flex h-9 w-9 items-center justify-center rounded-full text-fg/60 transition-colors hover:bg-fg/5 hover:text-fg"
          >
            <X size={20} />
          </button>
        </div>

        <ul className="mt-6 flex flex-1 flex-col overflow-y-auto px-6">
          {links.map((l) => (
            <li key={l.label}>
              <NavLink {...l} onNavigate={() => setOpen(false)} className={drawerLinkCls} />
            </li>
          ))}
        </ul>

        <div className="flex flex-col gap-3 border-t border-fg/8 px-6 py-6">
          <Link
            to="/signin"
            onClick={() => setOpen(false)}
            className="flex w-full items-center justify-center rounded-full border border-fg/20 py-3 text-button text-fg transition-colors hover:bg-fg/5"
          >
            Sign In
          </Link>
          <Link
            to="/signup"
            onClick={() => setOpen(false)}
            className="flex w-full items-center justify-center rounded-full bg-fg py-3 text-button text-cream transition-colors hover:bg-fg/85"
          >
            Get Started
          </Link>
        </div>
        </div>
      </div>
    </>
  );
}
