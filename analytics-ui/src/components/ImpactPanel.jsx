import { useAnalytics } from "../context/AnalyticsContext";

export function ImpactPanel() {
  const { impactStatement } = useAnalytics();

  return (
    <section className="panel p-6 bg-blue-600 text-white shadow-lg shadow-blue-500/20 border-0">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">📊</span>
        <h3 className="text-lg font-bold tracking-tight">System Impact</h3>
      </div>
      <p className="text-sm font-medium leading-relaxed text-blue-50 opacity-90 italic">
        "{impactStatement}"
      </p>
      <div className="mt-4 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-blue-200">
        <span>Grievance AI Analysis</span>
        <span>v1.0.0</span>
      </div>
    </section>
  );
}
