import { useEffect, useState } from "react";

export function MetricsPanel() {
  const [metrics, setMetrics] = useState({
    avg_resolution_hours: "—",
    resolved_today: 0,
    active_tickets: 0,
    total_resolved: 0,
    total_tickets: 0,
    resolution_rate: "0%",
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch("http://localhost:8000/analytics/metrics");
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (error) {
        console.debug("Failed to fetch metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    
    // Refresh metrics every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const metricCards = [
    {
      label: "Avg Resolution Time",
      value: metrics.avg_resolution_hours,
      unit: metrics.avg_resolution_hours === "N/A" ? "" : "hours",
      icon: "⏱️",
      highlight: true,
    },
    {
      label: "Resolved Today",
      value: metrics.resolved_today,
      unit: "tickets",
      icon: "✅",
      highlight: false,
    },
    {
      label: "Active Tickets",
      value: metrics.active_tickets,
      unit: "open",
      icon: "📋",
      highlight: false,
    },
    {
      label: "Resolution Rate",
      value: metrics.resolution_rate,
      unit: "",
      icon: "📊",
      highlight: false,
    },
  ];

  return (
    <section className="panel p-4">
      <h3 className="font-semibold mb-4 flex items-center gap-2">
        <span>📈 Operational Metrics</span>
        {loading && <span className="text-xs text-slate-500">(loading...)</span>}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metricCards.map((card, idx) => (
          <div
            key={idx}
            className={`rounded-lg p-3 text-center transition-all ${
              card.highlight
                ? "bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 shadow-sm"
                : "bg-slate-50 border border-slate-200"
            }`}
          >
            <div className="text-2xl mb-1">{card.icon}</div>
            <p className="text-xs text-slate-600 mb-1">{card.label}</p>
            <p className={`text-lg font-bold ${card.highlight ? "text-blue-700" : "text-slate-700"}`}>
              {typeof card.value === "number" ? card.value.toLocaleString() : card.value}
            </p>
            {card.unit && <p className="text-xs text-slate-500">{card.unit}</p>}
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500 mt-3 text-center">
        Total: {metrics.total_resolved.toLocaleString()} resolved of {metrics.total_tickets.toLocaleString()} tickets
      </p>
    </section>
  );
}
