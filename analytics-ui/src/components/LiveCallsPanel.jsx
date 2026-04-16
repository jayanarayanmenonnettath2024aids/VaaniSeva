import { useState } from "react";
import { useAnalytics } from "../context/AnalyticsContext";

/* ── helpers ─────────────────────────────────────────────────────────── */
const priorityStyle = {
  High:   "bg-rose-100 text-rose-700 border-rose-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low:    "bg-slate-100 text-slate-600 border-slate-200",
};

const statusStyle = (s) => {
  if (s.includes("Processing") || s.includes("Incoming")) return "text-amber-500";
  if (s.includes("Ticket") || s.includes("SMS"))           return "text-emerald-500";
  return "text-blue-500";
};

const bubbleStyle = {
  caller: { side: "justify-start", bg: "bg-slate-800 text-slate-100", label: "Caller" },
  ai:     { side: "justify-end",   bg: "bg-blue-600 text-white",       label: "AI" },
  system: { side: "justify-center",bg: "bg-slate-700/60 text-slate-400 text-[10px] italic font-medium rounded-lg px-3 py-1", label: "" },
};

function timeAgo(isoStr) {
  if (!isoStr) return "";
  const secs = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
  if (secs < 60)  return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

/* ── Call Detail Drawer ───────────────────────────────────────────────── */
function CallDrawer({ call, onClose }) {
  if (!call) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-all"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-lg z-50 bg-slate-900 shadow-2xl overflow-hidden flex flex-col animate-slide-up"
           style={{ animation: "none", transform: "none" }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Live Intelligence</span>
            </div>
            <h2 className="text-lg font-black text-white tracking-tight">Call #{call.ticket_id || call.id.slice(-6)}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-all text-lg"
          >
            ×
          </button>
        </div>

        {/* Caller meta */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-800/30">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-blue-500/30">
              {call.caller?.[0] || "?"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-base font-black text-white truncate">{call.caller}</p>
              <p className="text-[11px] text-slate-400 font-medium">{call.phone || "Unknown number"}</p>
            </div>
            <span className={`text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg border ${priorityStyle[call.priority] || priorityStyle.Low}`}>
              {call.priority || "—"} Priority
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            {[
              { label: "Language",   val: call.language    },
              { label: "Location",   val: call.location    },
              { label: "Department", val: call.department  },
              { label: "Duration",   val: call.duration    },
              { label: "Issue Type", val: call.issue_type  },
              { label: "Started",    val: timeAgo(call.started_at) },
            ].map((m) => (
              <div key={m.label} className="bg-slate-800/50 rounded-xl border border-slate-700/40 px-3 py-2.5">
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{m.label}</p>
                <p className="text-[12px] font-bold text-slate-200 mt-0.5 truncate">{m.val || "—"}</p>
              </div>
            ))}
          </div>

          {/* Status + ticket */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              <span className={`text-sm font-black ${statusStyle(call.status)}`}>● {call.status}</span>
            </div>
            {call.ticket_id && (
              <span className="text-[10px] font-black text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-lg uppercase tracking-widest">
                🎫 {call.ticket_id}
              </span>
            )}
          </div>
        </div>

        {/* Issue summary */}
        <div className="px-6 py-3 border-b border-slate-800">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Issue Summary</p>
          <p className="text-sm font-semibold text-slate-200 leading-snug">{call.issue}</p>
        </div>

        {/* Conversation transcript */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 custom-scrollbar">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">📞 Call Transcript</p>

          {(call.conversation || []).map((msg, i) => {
            const style = bubbleStyle[msg.role];
            if (msg.role === "system") {
              return (
                <div key={i} className={`flex ${style.side}`}>
                  <span className={style.bg}>{msg.text}</span>
                </div>
              );
            }
            return (
              <div key={i} className={`flex flex-col gap-1 ${style.side === "justify-end" ? "items-end" : "items-start"}`}>
                <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest px-1">
                  {msg.role === "ai" ? "🤖 VAANISEVA" : `👤 ${call.caller}`}
                </p>
                <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm font-medium leading-relaxed ${style.bg} shadow-sm`}>
                  {msg.text}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer actions */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/80">
          <div className="grid grid-cols-2 gap-3">
            <button className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-black text-[11px] uppercase tracking-widest py-3 rounded-xl transition-all shadow-lg shadow-blue-600/20">
              📋 View Ticket
            </button>
            <button className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-black text-[11px] uppercase tracking-widest py-3 rounded-xl transition-all">
              📤 Escalate
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

/* ── Live Calls Panel ─────────────────────────────────────────────────── */
export function LiveCallsPanel() {
  const { liveCalls, startDemoMode, runFullSystemDemo, demoScriptRunning, demoStepMessage } = useAnalytics();
  const [selectedCall, setSelectedCall] = useState(null);

  return (
    <>
      {/* Drawer */}
      {selectedCall && <CallDrawer call={selectedCall} onClose={() => setSelectedCall(null)} />}

      <section className="panel p-6 h-full flex flex-col">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="text-lg font-bold text-slate-800 tracking-tight">Live Operations</h3>
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mt-0.5">
              {liveCalls.length} Active Call{liveCalls.length !== 1 ? "s" : ""} · Tap a card for details
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={startDemoMode}
              className="rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 px-4 py-2 text-[10px] font-black uppercase tracking-wider transition-all shadow-sm"
            >
              + Demo Call
            </button>
            <button
              type="button"
              onClick={runFullSystemDemo}
              disabled={demoScriptRunning}
              className="rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:cursor-not-allowed text-white px-4 py-2 text-[10px] font-black uppercase tracking-wider transition-all shadow-md shadow-blue-500/20"
            >
              {demoScriptRunning ? "Running..." : "Full Audit"}
            </button>
          </div>
        </div>

        {/* Step message */}
        {demoStepMessage && demoStepMessage !== "Ready" && (
          <div className="mb-4 inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-700 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg self-start">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
            {demoStepMessage}
          </div>
        )}

        {/* Call cards */}
        <div className="space-y-3 flex-1 overflow-auto custom-scrollbar pr-1">
          {liveCalls.length === 0 && (
            <div className="py-16 text-center border border-dashed border-slate-200 rounded-2xl">
              <p className="text-2xl mb-2">📞</p>
              <p className="text-sm font-bold text-slate-400">No active calls right now</p>
              <button onClick={startDemoMode} className="mt-3 text-[10px] font-black text-blue-600 uppercase tracking-widest hover:underline">
                Simulate a call →
              </button>
            </div>
          )}

          {liveCalls.map((call) => (
            <button
              key={call.id}
              onClick={() => setSelectedCall(call)}
              className="w-full text-left group relative rounded-2xl border border-slate-100 bg-slate-50/50 p-4 transition-all hover:bg-white hover:border-slate-200 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {/* Live indicator */}
              <span className="absolute top-4 right-4 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>

              {/* Badge row */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
                  #{call.ticket_id || call.id.slice(-6)}
                </span>
                {call.priority && (
                  <span className={`text-[9px] font-black px-2 py-0.5 rounded-full border ${priorityStyle[call.priority] || priorityStyle.Low}`}>
                    {call.priority}
                  </span>
                )}
              </div>

              {/* Caller */}
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center font-black text-slate-600 text-sm group-hover:bg-blue-100 transition-colors">
                  {call.caller?.[0] || "?"}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-sm text-slate-800 truncate">{call.caller}</p>
                  <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider truncate">
                    {call.language} · {call.issue}
                  </p>
                </div>
              </div>

              {/* Footer row */}
              <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className={`text-[11px] font-black ${statusStyle(call.status)}`}>
                  {call.status}
                </span>
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                  <span>🕐</span>
                  <span>{call.duration || timeAgo(call.started_at)}</span>
                  <span className="text-slate-300">·</span>
                  <span className="text-blue-500 font-black">Tap for details →</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>
    </>
  );
}
