import { useEffect, useState } from "react";

import { useAnalytics } from "../context/AnalyticsContext";

function getCountdown(row, now) {
  const deadline = new Date(new Date(row.created_at).getTime() + row.sla_hours * 60 * 60 * 1000);
  const diffMs = deadline.getTime() - now.getTime();
  const abs = Math.abs(diffMs);
  const hours = Math.floor(abs / (1000 * 60 * 60));
  const minutes = Math.floor((abs % (1000 * 60 * 60)) / (1000 * 60));

  if (diffMs <= 0) {
    return { breached: true, text: `0h ${minutes}m (breached)` };
  }

  return { breached: false, text: `${hours}h ${minutes}m remaining` };
}

export function TicketTable({ compact = false }) {
  const { filteredComplaints } = useAnalytics();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  const rows = compact ? filteredComplaints.slice(0, 5) : filteredComplaints;

  return (
    <section className="panel overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div>
          <h3 className="font-bold text-slate-800 tracking-tight text-sm uppercase tracking-[0.1em]">Grievance Operations Registry</h3>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-0.5">Live Data Feed</p>
        </div>
        <div className="flex items-center gap-2">
           <span className="text-[11px] font-bold text-slate-400 tabular-nums">{rows.length} RECORD(S) FOUND</span>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[1000px]">
          <thead>
            <tr className="bg-white border-b border-slate-200">
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Tracking ID</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Context & Issue</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Department</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Status</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Jurisdiction</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest">Priority</th>
              <th className="px-6 py-4 text-[11px] font-bold text-slate-500 uppercase tracking-widest text-right">SLA Compliance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => {
              const countdown = getCountdown(row, now);
              return (
                <tr key={row.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4 text-xs font-bold text-blue-600 tabular-nums uppercase">{row.id}</td>
                  <td className="px-6 py-4">
                    <p className="text-sm font-bold text-slate-800 line-clamp-1">{row.issue}</p>
                    <p className="text-[10px] text-slate-500 font-medium uppercase mt-0.5">{row.issue_type}</p>
                  </td>
                  <td className="px-6 py-4">
                     <span className="text-xs font-bold text-slate-600">{row.department}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                      row.status === 'resolved' ? 'bg-emerald-100 text-emerald-700' :
                      row.status === 'assigned' ? 'bg-blue-100 text-blue-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {row.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-xs font-bold text-slate-700">{row.district}</p>
                    <p className="text-[10px] text-slate-500 font-medium uppercase">{row.state}</p>
                  </td>
                  <td className="px-6 py-4">
                     <span className={`text-[10px] font-black uppercase tracking-widest ${
                       row.priority === 'high' ? 'text-rose-600' :
                       row.priority === 'medium' ? 'text-amber-600' :
                       'text-slate-500'
                     }`}>
                       {row.priority}
                     </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className={`text-xs font-bold tabular-nums flex items-center justify-end gap-1.5 ${countdown.breached ? "text-rose-600" : "text-slate-600"}`}>
                      {countdown.breached ? (
                        <span className="flex h-2 w-2 rounded-full bg-rose-500"></span>
                      ) : (
                        <span className="flex h-2 w-2 rounded-full bg-blue-500"></span>
                      )}
                      {countdown.text}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {!compact && (
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/30">
          <button className="text-[11px] font-bold text-slate-500 uppercase tracking-widest hover:text-blue-600 transition-colors">← Previous</button>
          <div className="flex gap-2">
            {[1, 2, 3].map(p => (
              <button key={p} className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${p === 1 ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20' : 'text-slate-500 hover:bg-slate-100'}`}>{p}</button>
            ))}
          </div>
          <button className="text-[11px] font-bold text-slate-500 uppercase tracking-widest hover:text-blue-600 transition-colors">Next →</button>
        </div>
      )}
    </section>
  );
}
