import { useAnalytics } from "../context/AnalyticsContext";

export function InsightPanel() {
  const { insights, summary, regionPath } = useAnalytics();

  return (
    <section className="panel p-4 my-5">
      <h3 className="font-semibold mb-3">Live Storytelling Panel</h3>
      <div className="grid md:grid-cols-3 gap-3 text-sm">
        <article className="rounded-xl bg-slate-50 p-3 border border-slate-200">
          <p className="text-slate-500">Most affected region</p>
          <p className="font-semibold">{insights.topRegion}</p>
        </article>
        <article className="rounded-xl bg-slate-50 p-3 border border-slate-200">
          <p className="text-slate-500">Fastest growing issue</p>
          <p className="font-semibold">{insights.topIssue}</p>
        </article>
        <article className="rounded-xl bg-slate-50 p-3 border border-slate-200">
          <p className="text-slate-500">Highest SLA breach area</p>
          <p className="font-semibold">{regionPath.district || insights.topRegion}</p>
        </article>
      </div>
      <p className="mt-3 text-slate-700">
        {insights.narrative} Current unresolved load is {summary.unresolved} with {summary.breaches} SLA risks.
      </p>
      <ul className="mt-3 space-y-1 text-sm text-slate-700 list-disc pl-5">
        {insights.autoLines?.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </section>
  );
}
