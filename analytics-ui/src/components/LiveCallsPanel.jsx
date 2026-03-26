import { useAnalytics } from "../context/AnalyticsContext";

export function LiveCallsPanel() {
  const { liveCalls, startDemoMode, runFullSystemDemo, demoScriptRunning, demoStepMessage } = useAnalytics();

  return (
    <section className="panel p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Live Calls</h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={startDemoMode}
            className="rounded-lg bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 text-sm"
          >
            Start Demo Mode
          </button>
          <button
            type="button"
            onClick={runFullSystemDemo}
            disabled={demoScriptRunning}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white px-3 py-1.5 text-sm"
          >
            Run Full System Demo
          </button>
        </div>
      </div>

      <p className="text-sm text-indigo-700 mb-3">{demoStepMessage}</p>

      <div className="space-y-3">
        {liveCalls.map((call) => (
          <article key={call.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase text-slate-500 tracking-wider">Incoming</p>
            <p className="font-semibold">{call.caller} ({call.language})</p>
            <p className="text-sm mt-1">Issue: {call.issue}</p>
            <p className="text-sm text-emerald-700 mt-1">Status: {call.status}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
