import { useAnalytics } from "../context/AnalyticsContext";

export function AlertsPanel() {
  const { filteredComplaints } = useAnalytics();
  const breaches = filteredComplaints.filter((c) => c.breached);

  return (
    <section className="panel p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-slate-800 tracking-tight">Critical Alerts</h3>
        <span className="text-[10px] font-bold text-rose-600 uppercase tracking-widest bg-rose-50 px-2 py-1 rounded border border-rose-100">
          SLA Watch
        </span>
      </div>
      
      <div className="space-y-3 max-h-48 overflow-auto custom-scrollbar pr-1">
        {breaches.length === 0 ? (
          <div className="py-8 text-center border border-dashed border-slate-200 rounded-xl">
             <p className="text-sm text-slate-400 font-medium">No critical SLA breaches detected.</p>
          </div>
        ) : (
          breaches.map((ticket) => (
            <article key={ticket.id} className="relative rounded-xl border-l-4 border-rose-500 bg-rose-50/30 p-4 transition-all hover:bg-rose-50/50">
              <div className="flex justify-between items-start mb-1">
                <p className="text-xs font-bold text-rose-700 uppercase tracking-tight">{ticket.id}</p>
                <span className="text-[10px] font-bold text-slate-500 uppercase">Breached</span>
              </div>
              <p className="text-sm font-bold text-slate-800 leading-tight">Delayed in {ticket.district}</p>
              <p className="text-[11px] text-slate-600 font-medium mt-1">{ticket.issue_type} assigned to {ticket.department}</p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
