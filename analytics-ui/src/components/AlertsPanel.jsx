import { useAnalytics } from "../context/AnalyticsContext";

export function AlertsPanel() {
  const { filteredComplaints } = useAnalytics();
  const breaches = filteredComplaints.filter((c) => c.breached);

  return (
    <section className="panel p-4">
      <h3 className="font-semibold mb-3">Real-time Alerts</h3>
      <div className="space-y-2 max-h-48 overflow-auto">
        {breaches.length === 0 ? (
          <p className="text-sm text-slate-600">No active breach alerts in current filters.</p>
        ) : (
          breaches.map((ticket) => (
            <article key={ticket.id} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
              <p className="font-medium">{ticket.id} delayed in {ticket.district}</p>
              <p className="text-slate-700">{ticket.issue_type} issue assigned to {ticket.department}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
