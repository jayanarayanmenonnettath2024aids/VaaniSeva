import { useAnalytics } from "../context/AnalyticsContext";

export function KpiCards() {
  const { summary, lastUpdateAt } = useAnalytics();

  const cards = [
    ["Total Tickets", summary.total],
    ["Resolved", summary.resolved],
    ["Unresolved", summary.unresolved],
    ["SLA Breaches", summary.breaches],
    ["Resolution Rate", `${summary.resolutionRate}%`],
  ];

  return (
    <section key={lastUpdateAt} className="grid grid-cols-2 xl:grid-cols-5 gap-3 mb-5 fade-in-up">
      {cards.map(([label, value]) => (
        <article key={label} className="panel p-4">
          <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
          <p className="text-2xl font-semibold mt-1">{value}</p>
        </article>
      ))}
    </section>
  );
}
