import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FilePlus2,
  History,
  BookOpenText,
  Settings as SettingsIcon,
  LogOut,
} from "lucide-react";
import { CribraMark } from "../components/ui.jsx";
import data from "../data/mockData.json";

const NAV = [
  { to: "/app", end: true, icon: LayoutDashboard, label: "Dashboard" },
  { to: "/app/evaluations/new", icon: FilePlus2, label: "New Evaluation" },
  { to: "/app/evaluations", end: true, icon: History, label: "History" },
  { to: "/app/knowledge-base", icon: BookOpenText, label: "Knowledge Base" },
  { to: "/app/settings", icon: SettingsIcon, label: "Settings" },
];

export default function AppShell() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen bg-paper text-fg">
      <aside className="fixed inset-y-0 left-0 z-40 flex w-[232px] flex-col border-r border-dashed border-[var(--color-border)] bg-bg">
        <Link to="/" className="flex items-center gap-2 px-6 pt-7 pb-8">
          <CribraMark className="h-5 w-auto" />
          <span style={{ fontFamily: "var(--font-sans)", fontWeight: 500, fontSize: 17 }}>Cribra</span>
        </Link>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV.map(({ to, end, icon: Icon, label }) => (
            <NavLink
              key={label}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-full px-4 py-[9px] text-button transition-colors ${
                  isActive ? "bg-fg text-cream" : "text-fg/60 hover:bg-fg/5 hover:text-fg"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-dashed border-[var(--color-border)] px-6 py-5">
          <div className="text-button text-fg">{data.user.name}</div>
          <div className="text-caption text-fg/50" style={{ fontSize: 12 }}>
            {data.user.organisation}
          </div>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="text-button mt-3 flex items-center gap-2 text-fg/55 transition-colors hover:text-fg"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>
      <main className="ml-[232px] min-h-screen flex-1">
        <Outlet />
      </main>
    </div>
  );
}
