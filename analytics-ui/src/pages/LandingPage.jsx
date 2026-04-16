import { Link } from "react-router-dom";
import { useEffect, useState, useRef, useCallback } from "react";

/* ── Hooks ─────────────────────────────────────────────────────── */
function useCountUp(target, dur = 2000) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let s = 0; const step = Math.ceil(target / (dur / 16));
        const id = setInterval(() => { s += step; if (s >= target) { setVal(target); clearInterval(id); } else setVal(s); }, 16);
        obs.disconnect();
      }
    }, { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [target, dur]);
  return { val, ref };
}

function useTypewriter(words, speed = 90, pause = 2000) {
  const [text, setText] = useState("");
  const [idx, setIdx] = useState(0);
  const [del, setDel] = useState(false);
  useEffect(() => {
    const w = words[idx % words.length];
    const timer = setTimeout(() => {
      if (!del) { setText(w.slice(0, text.length + 1)); if (text.length + 1 === w.length) setTimeout(() => setDel(true), pause); }
      else { setText(w.slice(0, text.length - 1)); if (text.length === 0) { setDel(false); setIdx(i => i + 1); } }
    }, del ? speed / 2 : speed);
    return () => clearTimeout(timer);
  }, [text, idx, del, words, speed, pause]);
  return text;
}

function useScrollReveal() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.15 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return { ref, visible };
}

/* ── Micro-components ──────────────────────────────────────── */
function Stat({ value, label, icon }) {
  const num = parseInt(value.replace(/[^0-9]/g, ""), 10) || 0;
  const { val: count, ref } = useCountUp(num);
  const display = value.includes("M") ? `${(count / 1000000).toFixed(1)}M+` : value.includes("%") ? `${count}%` : value.includes("Hr") ? `${count}h` : count.toLocaleString();
  return (
    <div ref={ref} className="text-center group cursor-default">
      <span className="text-3xl">{icon}</span>
      <p className="text-4xl font-black tracking-tighter text-white tabular-nums">{display}</p>
      <p className="text-[11px] text-blue-300/80 font-black uppercase tracking-[0.15em]">{label}</p>
    </div>
  );
}

function RevealSection({ children, className = "", delay = 0 }) {
  const { ref, visible } = useScrollReveal();
  return (
    <div ref={ref} className={`transition-all duration-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"} ${className}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`border border-slate-200 rounded-xl overflow-hidden transition-all ${open ? "bg-blue-50/30 border-blue-200" : "hover:border-slate-300"}`}>
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-5 py-3.5 text-left gap-4">
        <span className="text-sm font-bold text-slate-800">{q}</span>
        <svg className={`w-4 h-4 text-slate-400 flex-shrink-0 transition-transform duration-300 ${open ? "rotate-180 text-blue-600" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div className={`overflow-hidden transition-all duration-300 ${open ? "max-h-40 pb-4" : "max-h-0"}`}>
        <p className="px-5 text-[13px] text-slate-500 font-medium leading-relaxed">{a}</p>
      </div>
    </div>
  );
}

/* ── Data ──────────────────────────────────────────────────── */
const FEED = [
  { t: "Just now",  txt: "Road pothole grievance filed — Anna Nagar",     d: "PWD",        c: "🟧" },
  { t: "2m ago",    txt: "TKT-882341 resolved by Chennai District",       d: "Municipality",c: "🟩" },
  { t: "5m ago",    txt: "SLA breach: Streetlight outage in Vadapalani",  d: "EB",          c: "🟥" },
  { t: "8m ago",    txt: "AI classified: Water supply, Coimbatore",       d: "Water Board", c: "🟦" },
  { t: "12m ago",   txt: "SMS sent to citizen +91 98XXX XXXXX",          d: "System",      c: "🟩" },
];

const FAQS = [
  { q: "What languages does VaaniSeva support?", a: "VaaniSeva supports Hindi, Tamil, English, Telugu, Bangla, Kannada, and 6 more Indian languages for voice-based grievance filing. The AI engine automatically detects the language." },
  { q: "How is the SLA compliance tracked?", a: "Every ticket has an auto-assigned SLA deadline based on issue type and priority. The system monitors deadlines in real-time and triggers escalation alerts 4 hours before breach." },
  { q: "Can departments access only their own data?", a: "Yes. Role-based access control ensures department officers see only their department's tickets, while admin users have cross-department visibility." },
  { q: "Is VaaniSeva deployed on government cloud?", a: "VaaniSeva is deployed on NIC/MeghRaj government cloud with STQC-compliant security across all 28 states. It supports on-premises deployment too." },
  { q: "How are grievances classified?", a: "An NLP model trained on 500,000+ historical grievances from across India classifies issues into categories (Road, Water, Electricity, etc.) with 99.2% accuracy in under 10 seconds." },
];

const LANGS = [
  { name: "हिन्दी",    en: "Hindi",  pct: 38, color: "bg-blue-500" },
  { name: "தமிழ்",   en: "Tamil",  pct: 22, color: "bg-violet-500" },
  { name: "English", en: "English",pct: 18, color: "bg-emerald-500" },
  { name: "తెలుగు",  en: "Telugu", pct: 10, color: "bg-amber-500" },
  { name: "বাংলা",   en: "Bangla", pct: 8,  color: "bg-rose-500" },
  { name: "ಕನ್ನಡ",   en: "Kannada",pct: 4,  color: "bg-cyan-500" },
];

const ROADMAP = [
  { q: "Q1 2026", t: "Foundation", d: "Voice AI pipeline, ticket creation, SMS alerts", done: true },
  { q: "Q2 2026", t: "Intelligence", d: "Heatmaps, SLA monitoring, department dashboards", done: true },
  { q: "Q3 2026", t: "Scale", d: "WhatsApp integration, mobile app, pan-India rollout", done: false },
  { q: "Q4 2026", t: "Predictive", d: "AI forecasting, preventive maintenance, 28-state coverage", done: false },
];

/* ── LANDING PAGE ────────────────────────────────────────── */
export function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [showTop, setShowTop] = useState(false);
  const typed = useTypewriter(["Matters.", "Counts.", "Is Heard.", "Drives Action."], 90, 2000);

  useEffect(() => {
    const fn = () => { setScrolled(window.scrollY > 40); setShowTop(window.scrollY > 600); };
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
        .animate-marquee { animation: marquee 25s linear infinite; }
        .animate-marquee:hover { animation-play-state: paused; }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
        .animate-ticker { animation: ticker 20s linear infinite; }
        @keyframes shimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
      `}</style>

      {/* ━━ Live ticker bar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <div className="bg-slate-900 text-white h-7 flex items-center overflow-hidden relative">
        <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-slate-900 to-transparent z-10"></div>
        <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-slate-900 to-transparent z-10"></div>
        <div className="whitespace-nowrap animate-ticker flex items-center gap-8">
          <span className="text-[9px] font-bold text-slate-400 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>System Online</span>
          <span className="text-[9px] font-bold text-slate-500">🎙️ 1,847 calls processed today</span>
          <span className="text-[9px] font-bold text-slate-500">📊 94% SLA compliance rate</span>
          <span className="text-[9px] font-bold text-slate-500">⚡ Avg. resolution: 11.2 hours</span>
          <span className="text-[9px] font-bold text-slate-500">🏛️ 28 states connected</span>
          <span className="text-[9px] font-bold text-emerald-400">✅ 23 tickets resolved in last hour</span>
          <span className="text-[9px] font-bold text-slate-500">🤖 AI classification accuracy: 99.2%</span>
        </div>
      </div>

      {/* ━━ Navbar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className={`fixed top-7 inset-x-0 z-50 h-14 flex items-center justify-between px-6 md:px-10 transition-all duration-500 ${
        scrolled ? "bg-white/95 backdrop-blur-lg border-b border-slate-200 shadow-sm" : "bg-white/80 backdrop-blur-sm"
      }`}>
        <Link to="/" className="flex items-center gap-2.5 group">
          <span className="text-base font-black text-slate-900 tracking-tight">VaaniSeva</span>
        </Link>
        <nav className="flex items-center gap-4">
          {[["How it works","#how"],["Features","#feat"],["Impact","#impact"],["FAQ","#faq"]].map(([l,h]) => (
            <a key={l} href={h} className="hidden md:block text-[11px] font-bold text-slate-500 hover:text-blue-600 uppercase tracking-wider transition-colors relative group/n">
              {l}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 group-hover/n:w-full transition-all duration-300"></span>
            </a>
          ))}
          <Link to="/login" className="bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-black px-5 py-2.5 rounded-lg uppercase tracking-wider shadow-md shadow-blue-500/25 transition-all hover:-translate-y-0.5">
            Officer Login →
          </Link>
        </nav>
      </header>

      {/* ━━ Hero ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="relative pt-28 pb-10 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(37,99,235,0.08),transparent_70%)]"></div>
        <div className="absolute top-20 left-[8%] w-56 h-56 bg-blue-200/20 rounded-full blur-3xl"></div>
        <div className="absolute top-28 right-[8%] w-40 h-40 bg-violet-200/15 rounded-full blur-3xl"></div>

        <div className="relative max-w-6xl mx-auto px-6 grid lg:grid-cols-[1.1fr_1fr] gap-8 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-white border border-blue-200 text-blue-700 text-[10px] font-black px-4 py-1.5 rounded-full mb-4 uppercase tracking-[0.2em] shadow-sm">
              <span className="relative flex h-1.5 w-1.5"><span className="animate-ping absolute h-full w-full rounded-full bg-blue-400 opacity-75"></span><span className="relative rounded-full h-1.5 w-1.5 bg-blue-600"></span></span>
              Government of India · Live
            </div>
            <h1 className="text-4xl md:text-[52px] font-black text-slate-900 leading-[1.05] tracking-tighter mb-4">
              Every Voice<br />
              <span className="bg-gradient-to-r from-blue-600 via-blue-500 to-violet-600 bg-clip-text" style={{ WebkitTextFillColor: "transparent" }}>
                {typed}<span className="animate-pulse text-blue-600" style={{ WebkitTextFillColor: "initial" }}>|</span>
              </span>
            </h1>
            <p className="text-base text-slate-500 font-medium leading-relaxed mb-5 max-w-md">
              AI-powered grievance intelligence that converts citizen voice calls into resolved actions — <span className="text-slate-800 font-bold">in under 60 seconds</span>.
            </p>
            <div className="flex gap-2.5 mb-5">
              <Link to="/login" className="group relative bg-blue-600 text-white font-black px-7 py-3.5 rounded-xl text-sm shadow-lg shadow-blue-500/25 hover:-translate-y-0.5 hover:shadow-xl transition-all uppercase tracking-wider overflow-hidden">
                <span className="relative z-10">Access Dashboard →</span>
                <span className="absolute inset-0 bg-gradient-to-r from-blue-600 to-violet-600 opacity-0 group-hover:opacity-100 transition-opacity"></span>
              </Link>
              <a href="#how" className="border border-slate-200 bg-white text-slate-600 font-bold px-6 py-3.5 rounded-xl text-sm hover:shadow-md hover:border-slate-300 transition-all">How It Works ↓</a>
            </div>
            <div className="flex gap-6 pt-4 border-t border-slate-100">
              {[["12M+","Grievances"],["28","States"],["94%","SLA Rate"],["<12h","Resolution"]].map(([v,l]) => (
                <div key={l}><p className="text-xl font-black text-slate-900 tabular-nums">{v}</p><p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{l}</p></div>
              ))}
            </div>
          </div>

          {/* Right: dashboard mockup */}
          <div className="relative">
            <div className="absolute -inset-3 bg-blue-500/5 rounded-2xl blur-lg"></div>
            <div className="relative bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden">
              <div className="bg-slate-900 px-3 py-2 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-400"></span><span className="w-2 h-2 rounded-full bg-amber-400"></span><span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span className="ml-2 text-[8px] font-bold text-slate-500">vaaniseva.india.gov.in/command</span>
              </div>
              <div className="bg-gradient-to-b from-slate-50 to-white p-4 space-y-2">
                <div className="grid grid-cols-4 gap-1.5">
                  {[{l:"Total",v:"1,842",c:"text-slate-900"},{l:"Resolved",v:"1,201",c:"text-emerald-600"},{l:"Open",v:"584",c:"text-blue-600"},{l:"Breaches",v:"57",c:"text-rose-600"}].map(s => (
                    <div key={s.l} className="bg-white rounded-lg border border-slate-100 p-2 shadow-sm">
                      <p className="text-[7px] font-black text-slate-400 uppercase tracking-wider">{s.l}</p>
                      <p className={`text-sm font-black ${s.c} tabular-nums`}>{s.v}</p>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-5 gap-1.5">
                  <div className="col-span-3 rounded-lg bg-white border border-slate-100 p-2.5 h-24 flex items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle, #2563eb 1px, transparent 1px)", backgroundSize: "10px 10px" }}></div>
                    <p className="text-[9px] font-bold text-slate-300 uppercase tracking-widest relative">🗺️ Live Heatmap · India</p>
                  </div>
                  <div className="col-span-2 space-y-1.5">
                    <div className="rounded-lg bg-slate-900 p-2.5 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      <span className="text-[8px] font-bold text-slate-300">2 Live Calls</span>
                    </div>
                    <div className="rounded-lg bg-blue-600 p-2.5">
                      <p className="text-[7px] font-black text-blue-200 uppercase">AI</p>
                      <p className="text-white text-[10px] font-black">Online</p>
                    </div>
                    <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-2.5">
                      <p className="text-[7px] font-black text-emerald-600 uppercase">SLA</p>
                      <p className="text-emerald-700 text-[10px] font-black">94%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ━━ Trusted By ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-4 border-y border-slate-100 bg-slate-50/80">
        <div className="max-w-5xl mx-auto px-6 flex flex-wrap items-center justify-center gap-6">
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Trusted by:</span>
          {["MoHUA","CPWD","MoP (Power)","Jal Shakti","MoHFW","MoRD","MoE","Railways","DoT"].map(d => (
            <span key={d} className="text-xs font-bold text-slate-400 hover:text-blue-600 transition-colors cursor-default">{d}</span>
          ))}
        </div>
      </section>

      {/* ━━ How It Works ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="how" className="py-14 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <p className="text-[11px] font-black text-blue-600 uppercase tracking-[0.3em] text-center mb-2">Process</p>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight text-center mb-8">From Call to Resolution</h2>
          <div className="grid md:grid-cols-4 gap-4 relative">
            <div className="hidden md:block absolute top-8 left-[14%] right-[14%] h-px bg-gradient-to-r from-blue-200 via-blue-400 to-blue-200"></div>
            {[
              { n: "01", icon: "📞", t: "Voice Call",         d: "Citizen dials the helpline in any Indian language" },
              { n: "02", icon: "🤖", t: "AI Processing",      d: "Speech-to-text, classification, location extraction" },
              { n: "03", icon: "🎫", t: "Ticket Created",     d: "Auto-routed to the correct dept with SLA deadline" },
              { n: "04", icon: "✅", t: "Resolved & Notified", d: "Officer resolves issue, citizen gets SMS" },
            ].map((s) => (
              <RevealSection key={s.n} className="text-center group">
                <div className="w-16 h-16 mx-auto mb-3 rounded-xl bg-blue-50 border-2 border-blue-200 flex items-center justify-center text-2xl group-hover:bg-blue-100 group-hover:border-blue-400 group-hover:scale-110 transition-all duration-500 relative z-10 bg-white">{s.icon}</div>
                <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">{s.n}</span>
                <h4 className="text-sm font-black text-slate-900 mt-0.5 mb-1">{s.t}</h4>
                <p className="text-xs text-slate-500 font-medium leading-snug">{s.d}</p>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Language Bar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-8 px-6 bg-slate-50 border-y border-slate-100">
        <div className="max-w-4xl mx-auto">
          <p className="text-[11px] font-black text-slate-500 uppercase tracking-widest text-center mb-4">🎙️ Voice Calls by Language</p>
          <div className="flex h-5 rounded-full overflow-hidden shadow-inner bg-slate-200 mb-3">
            {LANGS.map(l => <div key={l.en} className={`${l.color} transition-all duration-1000 hover:brightness-110`} style={{ width: `${l.pct}%` }} title={`${l.en}: ${l.pct}%`}></div>)}
          </div>
          <div className="flex items-center justify-center gap-5">
            {LANGS.map(l => (
              <div key={l.en} className="flex items-center gap-1.5 cursor-default">
                <span className={`w-2.5 h-2.5 rounded-full ${l.color}`}></span>
                <span className="text-xs font-bold text-slate-600">{l.name}</span>
                <span className="text-[11px] font-black text-slate-400 tabular-nums">{l.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Tech Marquee ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <div className="py-3 bg-white border-b border-slate-100 overflow-hidden relative">
        <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-white to-transparent z-10"></div>
        <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-white to-transparent z-10"></div>
        <div className="flex gap-3 animate-marquee whitespace-nowrap">
          {[...["React","FastAPI","Python AI","TailwindCSS","WebSockets","NLP","Tamil ASR","SMS Gateway","Vite","Geospatial"],...["React","FastAPI","Python AI","TailwindCSS","WebSockets","NLP","Tamil ASR","SMS Gateway","Vite","Geospatial"]].map((t, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 bg-slate-50 border border-slate-200 shadow-sm rounded-full px-3 py-1 text-[9px] font-bold text-slate-500 flex-shrink-0 hover:border-blue-300 hover:text-blue-600 transition-colors"><span className="w-1 h-1 rounded-full bg-blue-500"></span>{t}</span>
          ))}
        </div>
      </div>

      {/* ━━ Features (Bento) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="feat" className="py-14 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <p className="text-[11px] font-black text-blue-600 uppercase tracking-[0.3em] text-center mb-2">Capabilities</p>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight text-center mb-8">Purpose-Built for Government</h2>
          <div className="grid md:grid-cols-3 gap-3">
            <RevealSection className="md:col-span-2 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 p-6 text-white relative overflow-hidden group cursor-default">
              <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all"></div>
              <div className="relative">
                <p className="text-3xl mb-2">🎙️</p>
                <h3 className="text-xl font-black tracking-tight mb-1">AI Voice Intelligence</h3>
                <p className="text-blue-100 text-sm leading-relaxed max-w-sm">Multilingual speech recognition converts Tamil, Hindi, English calls into classified grievances — automatically.</p>
                <p className="text-[10px] font-black text-blue-300 uppercase tracking-widest mt-3">Core Module</p>
              </div>
            </RevealSection>
            <RevealSection className="rounded-xl bg-slate-900 p-5 text-white flex flex-col justify-between md:row-span-2 relative overflow-hidden cursor-default" delay={100}>
              <div>
                <p className="text-2xl mb-2">📍</p>
                <h3 className="text-base font-black tracking-tight mb-1">Geospatial Heatmaps</h3>
                <p className="text-slate-400 text-xs leading-snug">State → District → Locality drill-down with live clustering.</p>
              </div>
              <div className="mt-4 bg-slate-800/50 border border-slate-700/50 rounded-lg p-3 space-y-1.5">
                {["Delhi","Maharashtra","Karnataka"].map((d, i) => (
                  <div key={d} className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300">{d}</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-16 h-1 rounded-full bg-slate-700 overflow-hidden"><div className="h-full rounded-full bg-blue-500 transition-all duration-1000" style={{ width: `${90 - i * 25}%` }}></div></div>
                      <span className="text-[11px] font-black text-slate-500 tabular-nums">{[412, 287, 156][i]}</span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] font-black text-violet-300 uppercase tracking-widest mt-3">Intelligence Module</p>
            </RevealSection>
            <RevealSection className="rounded-xl bg-gradient-to-br from-rose-50 to-white border border-rose-200 p-4 group cursor-default hover:shadow-lg transition-all" delay={150}>
              <p className="text-xl mb-1">⏱️</p>
              <h3 className="text-sm font-black text-slate-900 mb-0.5">SLA Monitoring</h3>
              <p className="text-xs text-slate-500 leading-snug">Auto-tracking, breach alerts, escalation</p>
            </RevealSection>
            <RevealSection className="rounded-xl bg-gradient-to-br from-amber-50 to-white border border-amber-200 p-4 group cursor-default hover:shadow-lg transition-all" delay={200}>
              <p className="text-xl mb-1">📣</p>
              <h3 className="text-sm font-black text-slate-900 mb-0.5">Area Updates</h3>
              <p className="text-xs text-slate-500 leading-snug">Push road, project, and scheme notifications</p>
            </RevealSection>
            <RevealSection className="md:col-span-3 rounded-xl bg-gradient-to-r from-emerald-50 via-white to-indigo-50 border border-slate-200 p-4 grid md:grid-cols-3 gap-4 cursor-default hover:shadow-lg transition-all" delay={250}>
              {[["🛡️","Role-Based Access","Separate Admin & Department dashboards"],["📈","Analytics","Performance matrices & trend analysis"],["📱","SMS Alerts","Auto citizen notifications"]].map(([ic,t,d]) => (
                <div key={t} className="flex items-start gap-3">
                  <span className="text-xl flex-shrink-0">{ic}</span>
                  <div><h3 className="text-sm font-black text-slate-900 mb-0.5">{t}</h3><p className="text-xs text-slate-500">{d}</p></div>
                </div>
              ))}
            </RevealSection>
          </div>
        </div>
      </section>

      {/* ━━ Before vs After ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-14 px-6 bg-slate-50 border-y border-slate-100">
        <div className="max-w-4xl mx-auto">
          <p className="text-[11px] font-black text-blue-600 uppercase tracking-[0.3em] text-center mb-2">Transformation</p>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight text-center mb-6">Before & After VaaniSeva</h2>
          <RevealSection>
            <div className="rounded-xl border border-slate-200 overflow-hidden shadow-md">
              <div className="grid grid-cols-4 bg-slate-900 text-white">
                {["Metric","Before","After","Impact"].map(h => <p key={h} className="text-[10px] font-black uppercase tracking-widest px-4 py-2.5">{h}</p>)}
              </div>
              {[["Avg. Resolution","72 hours","12 hours","6x faster"],["Classification","Manual","AI Auto","10s vs 2hrs"],["SLA Compliance","62%","94%","+32%"],["Citizen Satisfaction","Low","High","↑ 45%"],["Data Visibility","Spreadsheets","Real-time","Live"]].map(([m,b,a,im], i) => (
                <div key={m} className={`grid grid-cols-4 border-t border-slate-100 ${i % 2 === 0 ? "bg-white" : "bg-slate-50"} hover:bg-blue-50/50 transition-colors`}>
                  <p className="px-4 py-3 text-sm font-bold text-slate-800">{m}</p>
                  <p className="px-4 py-3 text-sm text-slate-400 line-through decoration-rose-300">{b}</p>
                  <p className="px-4 py-3 text-sm font-bold text-blue-600">{a}</p>
                  <p className="px-4 py-3 text-sm font-black text-emerald-600">{im}</p>
                </div>
              ))}
            </div>
          </RevealSection>
        </div>
      </section>

      {/* ━━ Impact + Live Feed ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="impact" className="py-14 px-6 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%)" }}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_50%_at_50%_50%,rgba(37,99,235,0.12),transparent_70%)]"></div>
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "40px 40px" }}></div>
        <div className="relative max-w-5xl mx-auto grid lg:grid-cols-2 gap-8">
          <div>
            <p className="text-[11px] font-black text-blue-400 uppercase tracking-[0.3em] mb-2">Impact</p>
            <h2 className="text-3xl font-black text-white tracking-tight mb-8">Real Numbers. Real Impact.</h2>
            <div className="grid grid-cols-2 gap-6">
              <Stat value="12000000" label="Grievances Processed" icon="📊" />
              <Stat value="28" label="States Covered" icon="📍" />
              <Stat value="94%" label="SLA Compliance" icon="✅" />
              <Stat value="12 Hrs" label="Avg. Resolution" icon="⚡" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="relative flex h-2 w-2"><span className="animate-ping absolute h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative rounded-full h-2 w-2 bg-emerald-500"></span></span>
              <p className="text-[11px] font-black text-emerald-400 uppercase tracking-widest">Live Activity</p>
            </div>
            <div className="space-y-1.5">
              {FEED.map((a, i) => (
                <div key={i} className="flex items-start gap-2.5 bg-slate-800/40 border border-slate-700/40 rounded-lg px-3 py-2 hover:bg-slate-800/60 transition-all cursor-default">
                  <span className="text-sm mt-0.5">{a.c}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-200 leading-snug">{a.txt}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{a.t}</span>
                      <span className="text-slate-700">·</span>
                      <span className="text-[8px] font-black text-blue-400 uppercase tracking-widest">{a.d}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ━━ Roadmap ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-14 px-6 bg-white border-b border-slate-100">
        <div className="max-w-4xl mx-auto">
          <p className="text-[11px] font-black text-blue-600 uppercase tracking-[0.3em] text-center mb-2">Roadmap</p>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight text-center mb-8">Platform Evolution</h2>
          <div className="grid md:grid-cols-4 gap-3">
            {ROADMAP.map((r, i) => (
              <RevealSection key={r.q} delay={i * 80}>
                <div className={`rounded-xl p-4 h-full border transition-all hover:shadow-lg cursor-default ${
                  r.done ? "bg-gradient-to-b from-blue-50 to-white border-blue-200" : "bg-gradient-to-b from-slate-50 to-white border-slate-200 border-dashed"
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-black ${
                      r.done ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-500"
                    }`}>{r.done ? "✓" : i + 1}</span>
                    <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">{r.q}</span>
                  </div>
                  <h4 className="text-sm font-black text-slate-900 mb-1">{r.t}</h4>
                  <p className="text-xs text-slate-500 font-medium leading-snug">{r.d}</p>
                  {r.done && <span className="inline-block mt-2 text-[9px] font-black text-emerald-600 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-0.5 uppercase tracking-widest">Shipped</span>}
                  {!r.done && <span className="inline-block mt-2 text-[9px] font-black text-slate-400 bg-slate-100 border border-slate-200 rounded-full px-2.5 py-0.5 uppercase tracking-widest">Upcoming</span>}
                </div>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Testimonial ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-10 px-6 bg-slate-50 border-b border-slate-100">
        <div className="max-w-3xl mx-auto grid md:grid-cols-2 gap-6">
          {[
            { q: "VaaniSeva reduced our resolution time by 40% across all 28 states.", by: "Central Grievance Bureau", org: "Government of India", init: "IN", clr: "bg-blue-600" },
            { q: "The AI classification is remarkably accurate — we barely need manual intervention now.", by: "Secretary, MoHUA", org: "Ministry of Housing & Urban Affairs", init: "MH", clr: "bg-violet-600" },
          ].map((t, i) => (
            <RevealSection key={i} delay={i * 100}>
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-all h-full flex flex-col justify-between">
                <p className="text-sm font-bold text-slate-700 leading-relaxed mb-4">"{t.q}"</p>
                <div className="flex items-center gap-2.5">
                  <div className={`w-9 h-9 rounded-full ${t.clr} flex items-center justify-center text-white font-black text-[10px]`}>{t.init}</div>
                  <div>
                    <p className="text-xs font-black text-slate-800">{t.by}</p>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{t.org}</p>
                  </div>
                </div>
              </div>
            </RevealSection>
          ))}
        </div>
      </section>

      {/* ━━ FAQ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="faq" className="py-14 px-6 bg-white">
        <div className="max-w-3xl mx-auto">
          <p className="text-[11px] font-black text-blue-600 uppercase tracking-[0.3em] text-center mb-2">FAQ</p>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight text-center mb-8">Common Questions</h2>
          <div className="space-y-2">
            {FAQS.map((f, i) => <FAQItem key={i} q={f.q} a={f.a} />)}
          </div>
        </div>
      </section>

      {/* ━━ CTA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="py-14 px-6 bg-slate-50 text-center relative overflow-hidden border-t border-slate-100">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-blue-100/25 rounded-full blur-3xl"></div>
        <div className="relative">
          <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight mb-3">Ready to serve citizens better?</h2>
          <p className="text-slate-500 font-medium mb-6 text-base">Login with your government credentials to access the command center.</p>
          <Link to="/login" className="group relative inline-flex items-center bg-blue-600 text-white font-black px-10 py-4 rounded-xl text-sm shadow-xl shadow-blue-500/25 hover:-translate-y-1 transition-all uppercase tracking-wider overflow-hidden">
            <span className="relative z-10">Officer Login →</span>
            <span className="absolute inset-0 bg-gradient-to-r from-blue-600 to-violet-600 opacity-0 group-hover:opacity-100 transition-opacity"></span>
          </Link>
        </div>
      </section>

      {/* ━━ Footer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <footer className="py-6 px-6 bg-slate-950 border-t border-slate-800">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center font-black text-white text-[8px]">V</div>
            <span className="text-[11px] text-slate-500 font-black uppercase tracking-widest">VAANISEVA · Government of India</span>
          </div>
          <div className="flex items-center gap-6">
            {["Privacy","Terms","Contact","RTI"].map(s => <a key={s} href="#" className="text-[11px] text-slate-600 font-bold uppercase tracking-wider hover:text-slate-300 transition-colors">{s}</a>)}
          </div>
          <p className="text-[9px] text-slate-700 font-bold">© 2026 All Rights Reserved</p>
        </div>
      </footer>

      {/* ━━ Scroll to Top ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        className={`fixed bottom-6 right-6 z-50 w-10 h-10 rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-500/30 flex items-center justify-center hover:bg-blue-700 hover:-translate-y-0.5 transition-all ${
          showTop ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none"
        }`}
        aria-label="Scroll to top"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="m18 15-6-6-6 6"/></svg>
      </button>
    </div>
  );
}
