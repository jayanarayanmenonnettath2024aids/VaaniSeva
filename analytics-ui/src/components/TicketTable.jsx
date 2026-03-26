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
    <section className="panel p-4 overflow-auto">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">Ticket Operations Panel</h3>
        <span className="text-sm text-slate-500">{rows.length} rows</span>
      </div>
      <table className="w-full text-sm min-w-[900px]">
        <thead>
          <tr className="text-left border-b border-slate-200">
            <th className="py-2">ID</th>
            <th>Issue</th>
            <th>Type</th>
            <th>Department</th>
            <th>Status</th>
            <th>State</th>
            <th>District</th>
            <th>Priority</th>
            <th>SLA Timer</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const countdown = getCountdown(row, now);
            return (
              <tr key={row.id} className="border-b border-slate-100">
                <td className="py-2">{row.id}</td>
                <td>{row.issue}</td>
                <td>{row.issue_type}</td>
                <td>{row.department}</td>
                <td className="capitalize">{row.status}</td>
                <td>{row.state}</td>
                <td>{row.district}</td>
                <td className="uppercase">{row.priority}</td>
                <td className={countdown.breached ? "text-red-600 font-semibold" : "text-slate-700"}>
                  {countdown.breached ? "🔴 " : "⏳ "}
                  {countdown.text}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
