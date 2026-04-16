import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DEMO = [
  { username: "admin",       password: "admin123", label: "National Admin",     role: "Admin",        icon: "🛡️", color: "blue"   },
  { username: "pwd",         password: "pwd123",   label: "PWD Department",     role: "Dept Officer", icon: "🏗️", color: "emerald"},
  { username: "electricity", password: "elec123",  label: "Electricity Board",  role: "Dept Officer", icon: "⚡", color: "amber"  },
  { username: "sanitation",  password: "san123",   label: "Sanitation Dept.",   role: "Dept Officer", icon: "♻️", color: "violet" },
];

const chipColors = {
  blue:   "bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 hover:border-blue-400",
  emerald:"bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100 hover:border-emerald-400",
  amber:  "bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100 hover:border-amber-400",
  violet: "bg-violet-50 border-violet-200 text-violet-700 hover:bg-violet-100 hover:border-violet-400",
};

export function LoginPage() {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [showPwd, setShowPwd] = useState(false);
  const [selected, setSelected] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const user = await login(form.username, form.password);
    if (user) {
      navigate(user.role === "admin" ? "/admin" : "/department", { replace: true });
    }
  };

  const fillDemo = (acc) => {
    setForm({ username: acc.username, password: acc.password });
    setSelected(acc.username);
  };

  return (
    <div className="min-h-screen flex" style={{ fontFamily: "'Inter', sans-serif" }}>

      {/* ── Left / Branding ──────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 relative overflow-hidden"
           style={{ background: "linear-gradient(145deg, #0f172a 0%, #1e3a8a 55%, #0f172a 100%)" }}>

        {/* decorative orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-72 h-72 bg-violet-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl"></div>

        {/* Logo */}
        <Link to="/" className="relative flex items-center gap-3 group w-fit">
          <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center font-black text-white shadow-xl shadow-blue-600/40 group-hover:scale-105 transition-transform">V</div>
          <div>
            <p className="font-black text-white text-xl tracking-tight">VAANISEVA</p>
            <p className="text-[9px] text-blue-400 font-black uppercase tracking-[0.25em]">Gov Intelligence</p>
          </div>
        </Link>

        {/* Hero text */}
        <div className="relative">
          <div className="inline-flex items-center gap-2 bg-blue-600/20 border border-blue-500/30 text-blue-300 text-[9px] font-black px-3 py-1 rounded-full mb-6 uppercase tracking-[0.2em]">
            🔒 Secure Official Portal
          </div>
          <h2 className="text-4xl xl:text-5xl font-black text-white leading-[1.1] tracking-tight mb-5">
            Empowering Officers.<br />
            <span style={{ background: "linear-gradient(90deg, #60a5fa, #a78bfa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Resolving&nbsp;Faster.
            </span>
          </h2>
          <p className="text-slate-400 text-base font-medium leading-relaxed max-w-sm">
            Access your personalised command center to track SLAs, monitor grievances, and resolve citizen issues with AI intelligence.
          </p>
        </div>

        {/* Stats grid */}
        <div className="relative grid grid-cols-2 gap-3">
          {[
            { v: "247",   l: "Live Calls Today",  c: "text-blue-300"   },
            { v: "1,842", l: "Open Tickets",       c: "text-white"      },
            { v: "94%",   l: "SLA Compliance",     c: "text-emerald-300"},
            { v: "98.6%", l: "AI Accuracy",        c: "text-violet-300" },
          ].map((s) => (
            <div key={s.l} className="rounded-2xl border border-white/8 p-5" style={{ background: "rgba(255,255,255,0.05)" }}>
              <p className={`text-2xl font-black ${s.c}`}>{s.v}</p>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-1">{s.l}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Right / Form ─────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center bg-white p-8 md:p-12">
        <div className="w-full max-w-[420px]">

          {/* Mobile logo */}
          <Link to="/" className="lg:hidden flex items-center gap-2.5 mb-10">
            <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center font-black text-white text-sm">V</div>
            <span className="font-black text-slate-900 text-lg">VAANISEVA</span>
          </Link>

          {/* Heading */}
          <div className="mb-8">
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Welcome back</h1>
            <p className="text-slate-500 font-medium mt-1.5 text-sm">Sign in to your government portal</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 p-4 rounded-xl bg-rose-50 border border-rose-200 flex gap-3 items-start">
              <span className="text-rose-400 text-lg flex-shrink-0">⚠</span>
              <p className="text-sm font-semibold text-rose-700 leading-snug">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] mb-1.5">
                Officer ID / Username
              </label>
              <input
                id="username"
                type="text"
                required
                autoComplete="username"
                placeholder="e.g. admin"
                value={form.username}
                onChange={(e) => { setForm(f => ({ ...f, username: e.target.value })); setSelected(null); }}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-slate-900 font-semibold text-sm placeholder:text-slate-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white transition-all"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-[10px] font-black text-slate-500 uppercase tracking-[0.15em] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPwd ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5 pr-12 text-slate-900 font-semibold text-sm placeholder:text-slate-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 transition-colors"
                  tabIndex={-1}
                  aria-label="Toggle password visibility"
                >
                  {showPwd ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:cursor-not-allowed text-white font-black py-4 rounded-xl text-sm uppercase tracking-widest shadow-xl shadow-blue-500/25 hover:shadow-2xl hover:shadow-blue-500/35 transition-all hover:-translate-y-0.5 mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  Authenticating...
                </span>
              ) : "Sign In →"}
            </button>
          </form>

          {/* Quick-fill demo accounts */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-center mb-4">
              ⚡ Quick Access — Demo Accounts
            </p>
            <div className="grid grid-cols-2 gap-2.5">
              {DEMO.map((a) => (
                <button
                  key={a.username}
                  onClick={() => fillDemo(a)}
                  className={`flex items-center gap-2.5 p-3.5 rounded-xl border text-left transition-all ${chipColors[a.color]} ${selected === a.username ? "ring-2 ring-offset-1 ring-blue-500" : ""}`}
                >
                  <span className="text-xl flex-shrink-0">{a.icon}</span>
                  <div className="min-w-0">
                    <p className="text-[10px] font-black uppercase tracking-wider opacity-70">{a.role}</p>
                    <p className="text-xs font-bold truncate">{a.label}</p>
                  </div>
                </button>
              ))}
            </div>
            <p className="text-center text-[10px] text-slate-400 font-medium mt-3">
              Click a card to auto-fill · then press Sign In
            </p>
          </div>

          <Link to="/" className="block text-center mt-7 text-[10px] font-black text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-widest">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
