import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAnalytics } from "../context/AnalyticsContext";
import { useAuth } from "../context/AuthContext";
import { GlobalFilters } from "./GlobalFilters";

const nav = [
  { label: "Admin", role: "admin", items: [
    ["🏠 Command Center",         "/admin"],
    ["🗺️ Geographic Intelligence", "/admin/geography"],
    ["🔍 Issue Intelligence",     "/admin/issues"],
    ["⏱️ SLA & Risk",             "/admin/sla"],
    ["📈 Performance",            "/admin/performance"],
  ] },
  { label: "Operations", role: "department", items: [
    ["📊 Overview",               "/department"],
    ["🔥 Heatmap",                "/department/heatmap"],
    ["🎫 Tickets",                "/department/tickets"],
    ["📈 Performance",            "/department/performance"],
  ] },
];

/* ── Live Clock ───────────────────────────────────────────────── */
function LiveClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const pad = (n) => String(n).padStart(2, "0");
  const h = pad(now.getHours());
  const m = pad(now.getMinutes());
  const s = pad(now.getSeconds());
  const day = now.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/40 px-4 py-3">
      <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">🕐 Current Time</p>
      <p className="text-xl font-black text-white tracking-tighter tabular-nums">
        {h}:{m}<span className="text-slate-500">:{s}</span>
      </p>
      <p className="text-[10px] text-slate-500 font-bold mt-0.5">{day}</p>
    </div>
  );
}

/* ── Quick Stats ──────────────────────────────────────────────── */
function QuickStats() {
  const { summary, liveCalls } = useAnalytics();
  const stats = [
    { label: "Calls Today",    val: liveCalls.length, color: "text-blue-400"   },
    { label: "Open Tickets",   val: summary.unresolved ?? 0,  color: "text-amber-400"  },
    { label: "SLA Breaches",   val: summary.breaches  ?? 0,  color: "text-rose-400"   },
    { label: "Resolved",       val: summary.resolved  ?? 0,  color: "text-emerald-400"},
  ];

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/40 px-4 py-3">
      <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-3">📊 Today's Overview</p>
      <div className="grid grid-cols-2 gap-2">
        {stats.map((s) => (
          <div key={s.label} className="bg-slate-800/60 rounded-lg px-2.5 py-2 border border-slate-700/30">
            <p className={`text-base font-black tabular-nums ${s.color}`}>{s.val}</p>
            <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider leading-tight mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── System Status ────────────────────────────────────────────── */
function SystemStatus() {
  const services = [
    { label: "AI Engine",    status: "Online",    color: "bg-emerald-500", text: "text-emerald-400" },
    { label: "Voice Hub",    status: "Active",    color: "bg-emerald-500", text: "text-emerald-400" },
    { label: "Backend API",  status: "Connected", color: "bg-emerald-500", text: "text-emerald-400" },
    { label: "SLA Monitor",  status: "Running",   color: "bg-blue-500",    text: "text-blue-400"    },
  ];

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/40 px-4 py-3">
      <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-3">⚙️ System Status</p>
      <div className="space-y-2">
        {services.map((s) => (
          <div key={s.label} className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400">{s.label}</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${s.color} animate-pulse`}></span>
              <span className={`text-[9px] font-black uppercase tracking-wider ${s.text}`}>{s.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── AppShell ─────────────────────────────────────────────────── */
export function AppShell({ children, title, subtitle }) {
  const location = useLocation();
  const navigate  = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const visibleNav = nav.filter((s) => s.role === user?.role);

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[288px_1fr] bg-slate-50">

      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside className="bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 sticky top-0 h-screen overflow-y-auto custom-scrollbar">

        {/* Logo + Title */}
        <div className="p-5 border-b border-slate-800/50 flex-shrink-0">
          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white shadow-lg shadow-blue-500/25">V</div>
            <p className="text-xs uppercase tracking-[0.2em] font-black text-blue-400">VAANISEVA</p>
          </div>
          <h1 className="text-lg font-black tracking-tight text-white leading-snug">
            {user?.role === "department" ? `${user.department || "Operations"} Workspace` : "Command Center"}
          </h1>
          <p className="text-slate-500 text-[9px] uppercase font-black tracking-wider mt-0.5">Unified Service Intelligence</p>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 flex-shrink-0">
          <p className="text-[9px] uppercase font-black text-slate-600 mb-3 px-2 tracking-widest">Navigation</p>
          {visibleNav.flatMap((section) =>
            section.items.map(([label, path]) => {
              const active = location.pathname === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200 ${
                    active
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${active ? "bg-white" : "bg-slate-700 group-hover:bg-slate-500"}`}></span>
                  {label}
                </Link>
              );
            })
          )}
        </nav>

        {/* Widgets */}
        <div className="px-4 pb-3 space-y-3 flex-shrink-0">
          <div className="border-t border-slate-800/50 pt-4">
            <LiveClock />
          </div>
          <QuickStats />
          <SystemStatus />
        </div>

        {/* User Card + Logout */}
        <div className="p-4 border-t border-slate-800/50 space-y-2 flex-shrink-0 mt-auto">
          <div className="rounded-xl bg-slate-800/50 border border-slate-700/30 p-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-black text-white text-sm shadow-md shadow-blue-500/30">
                {user?.name?.[0] || "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-black text-slate-200 truncate">{user?.name || "Officer"}</p>
                <p className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">{user?.department || user?.role}</p>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-700 text-slate-400 hover:bg-rose-900/20 hover:text-rose-400 hover:border-rose-800/50 text-[10px] font-black uppercase tracking-widest py-2.5 transition-all"
          >
            🚪 Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-h-screen overflow-hidden">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm shadow-slate-200/50 flex-shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <h2 className="text-lg font-black text-slate-900 tracking-tight truncate">{title}</h2>
            <div className="h-4 w-px bg-slate-200 flex-shrink-0"></div>
            <p className="text-sm text-slate-500 font-medium truncate hidden sm:block">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[10px] font-black uppercase text-emerald-700 tracking-wider">Live</span>
            </div>
            {user && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-black text-white text-xs shadow">
                  {user.name?.[0] || "U"}
                </div>
                <div className="hidden sm:block text-right">
                  <p className="text-xs font-black text-slate-800">{user.name}</p>
                  <p className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">{user.department || user.role}</p>
                </div>
              </div>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-[1600px] mx-auto space-y-8">
            <GlobalFilters />
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
