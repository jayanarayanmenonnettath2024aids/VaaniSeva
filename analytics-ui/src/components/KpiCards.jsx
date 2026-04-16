import { useAnalytics } from "../context/AnalyticsContext";

export function KpiCards() {
  const { summary, lastUpdateAt } = useAnalytics();

  const cards = [
    { label: "Total Tickets", value: summary.total, icon: "📊", color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Resolved", value: summary.resolved, icon: "✅", color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Unresolved", value: summary.unresolved, icon: "⏳", color: "text-amber-600", bg: "bg-amber-50" },
    { label: "SLA Breaches", value: summary.breaches, icon: "⚠️", color: "text-rose-600", bg: "bg-rose-50" },
    { label: "Resolution Rate", value: `${summary.resolutionRate || 0}%`, icon: "📈", color: "text-indigo-600", bg: "bg-indigo-50" },
  ];

  return (
    <section key={lastUpdateAt} className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-6 animate-slide-up">
      {cards.map((card) => (
        <article key={card.label} className="kpi-card group cursor-default">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-[11px] uppercase font-bold text-slate-500 tracking-widest mb-1">{card.label}</p>
              <p className="text-3xl font-bold text-slate-900 tracking-tight">{card.value}</p>
            </div>
            <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center text-xl shadow-sm border border-white/50`}>
              {card.icon}
            </div>
          </div>
          <div className="mt-4 flex items-center text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
             <span className="text-emerald-500 mr-1">↑ 12%</span> vs last month
          </div>
          
          {/* Subtle Accent Bar */}
          <div className="absolute bottom-0 left-0 w-full h-1 bg-slate-100 group-hover:bg-blue-500/10 transition-colors"></div>
        </article>
      ))}
    </section>
  );
}
