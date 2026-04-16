import { useAnalytics } from "../context/AnalyticsContext";

export function AreaUpdatesPanel() {
  const { notifications } = useAnalytics();

  return (
    <section className="panel p-6 bg-slate-900 text-white relative overflow-hidden group">
       {/* Background Accent */}
      <div className="absolute -right-8 -top-8 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
      
      <div className="flex justify-between items-center mb-6 relative z-10">
        <div>
          <h3 className="font-bold text-lg tracking-tight text-white">Area Intelligence</h3>
          <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mt-0.5">Local Project Updates</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-[10px] uppercase font-bold text-emerald-400">Live</span>
        </div>
      </div>

      <div className="space-y-4 max-h-[350px] overflow-auto pr-2 custom-scrollbar relative z-10">
        {notifications.length === 0 ? (
          <div className="py-12 text-center rounded-xl border border-dashed border-slate-700">
            <p className="text-sm text-slate-500 font-medium italic">No active area intelligence reports.</p>
          </div>
        ) : (
          notifications.map((notif) => (
            <article key={notif.id} className="group/item relative rounded-xl bg-slate-800/40 border border-slate-700/50 p-4 hover:bg-slate-800/80 transition-all duration-300">
              <div className="flex justify-between items-start mb-3">
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-widest border ${
                  notif.category === 'Road' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                  notif.category === 'Education' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                  'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                }`}>
                  {notif.category}
                </span>
                <span className="text-[10px] text-slate-500 font-bold tabular-nums">
                  {new Date(notif.created_at).toLocaleDateString()}
                </span>
              </div>
              
              <h4 className="font-bold text-sm mb-1.5 group-hover/item:text-blue-400 transition-colors uppercase tracking-tight">
                {notif.title}
              </h4>
              
              <p className="text-[12px] text-slate-400 leading-relaxed mb-3 font-medium">
                {notif.description}
              </p>
              
              <div className="flex items-center text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                <svg className="w-3.5 h-3.5 mr-1.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                {notif.location}
              </div>
            </article>
          ))
        )}
      </div>
      
      <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
        <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Grievance AI Intelligence</span>
        <button className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors font-bold uppercase tracking-widest flex items-center gap-1">
          Archive <span className="text-lg">→</span>
        </button>
      </div>
    </section>
  );
}
