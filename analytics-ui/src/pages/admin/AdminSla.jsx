import { useAnalytics } from "../../context/AnalyticsContext";
import { AlertsPanel } from "../../components/AlertsPanel";
import { AppShell } from "../../components/AppShell";
import { KpiCards } from "../../components/KpiCards";

export function AdminSla() {
  const { filteredComplaints } = useAnalytics();
  const delayed = filteredComplaints.filter((c) => c.breached);

  return (
    <AppShell title="SLA & Risk Monitoring" subtitle="Breach tracking, risk zones, and delayed department visibility.">
      <KpiCards />
      <section className="grid lg:grid-cols-[1.2fr_1fr] gap-4">
        <article className="panel p-4">
          <h3 className="font-semibold mb-3">Delayed Departments</h3>
          <div className="space-y-2">
            {delayed.length === 0 ? (
              <p className="text-sm text-slate-600">No delayed complaints under current filters.</p>
            ) : (
              delayed.map((d) => (
                <div key={d.id} className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm">
                  <p className="font-medium">{d.department} | {d.id}</p>
                  <p>{d.state} / {d.district} | {d.issue_type}</p>
                </div>
              ))
            )}
          </div>
        </article>
        <AlertsPanel />
      </section>
    </AppShell>
  );
}
