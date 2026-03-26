import { Link, useLocation } from "react-router-dom";

import { useAnalytics } from "../context/AnalyticsContext";
import { GlobalFilters } from "./GlobalFilters";

const nav = [
  { label: "Admin", items: [
    ["Command Center", "/admin"],
    ["Geographic Intelligence", "/admin/geography"],
    ["Issue Intelligence", "/admin/issues"],
    ["SLA & Risk", "/admin/sla"],
    ["Performance", "/admin/performance"],
  ] },
  { label: "Department", items: [
    ["Overview", "/department"],
    ["Heatmap", "/department/heatmap"],
    ["Tickets", "/department/tickets"],
    ["Performance", "/department/performance"],
  ] },
  { label: "Public", items: [
    ["Public Heatmap", "/public"],
    ["Explorer", "/public/explorer"],
    ["Trends", "/public/trends"],
  ] },
];

export function AppShell({ children, title, subtitle }) {
  const location = useLocation();
  const { systemStatus } = useAnalytics();

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[280px_1fr]">
      <aside className="bg-ink text-slate-100 p-5">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-300">PALLAVI</p>
          <h1 className="text-2xl font-semibold">Command Center</h1>
          <p className="text-slate-400 text-sm">National AI grievance analytics</p>
        </div>

        <nav className="space-y-6">
          {nav.map((section) => (
            <div key={section.label}>
              <p className="text-xs uppercase text-slate-400 mb-2">{section.label}</p>
              <ul className="space-y-1">
                {section.items.map(([label, path]) => {
                  const active = location.pathname === path;
                  return (
                    <li key={path}>
                      <Link
                        to={path}
                        className={`block rounded-lg px-3 py-2 text-sm transition ${
                          active ? "bg-emerald-500 text-white" : "hover:bg-slate-800 text-slate-200"
                        }`}
                      >
                        {label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <main className="p-4 md:p-6 lg:p-8">
        <section className="panel p-3 mb-4">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <p><span className="text-green-600">●</span> AI Engine: {systemStatus.aiEngine}</p>
            <p><span className="text-green-600">●</span> Call System: {systemStatus.callSystem}</p>
            <p><span className="text-green-600">●</span> SLA Monitor: {systemStatus.slaMonitor}</p>
          </div>
        </section>
        <header className="mb-5">
          <h2 className="text-2xl md:text-3xl font-semibold text-slate-900">{title}</h2>
          <p className="text-slate-600 mt-1">{subtitle}</p>
        </header>
        <GlobalFilters />
        {children}
      </main>
    </div>
  );
}
