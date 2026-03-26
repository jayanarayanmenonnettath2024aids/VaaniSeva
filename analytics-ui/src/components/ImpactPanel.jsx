import { useAnalytics } from "../context/AnalyticsContext";

export function ImpactPanel() {
  const { impactStatement } = useAnalytics();

  return (
    <section className="panel p-4">
      <h3 className="text-lg font-semibold mb-2">Impact</h3>
      <p className="text-sm text-slate-700">{impactStatement}</p>
    </section>
  );
}
