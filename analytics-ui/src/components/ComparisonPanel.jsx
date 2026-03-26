import { useMemo, useState } from "react";

import { useAnalytics } from "../context/AnalyticsContext";

export function ComparisonPanel({ mode = "state" }) {
  const { complaints } = useAnalytics();

  const options = useMemo(() => {
    const key = mode === "state" ? "state" : "department";
    return [...new Set(complaints.map((c) => c[key]))];
  }, [complaints, mode]);

  const [left, setLeft] = useState(options[0] || "");
  const [right, setRight] = useState(options[1] || options[0] || "");

  const key = mode === "state" ? "state" : "department";
  const getCount = (name) => complaints.filter((c) => c[key] === name).length;

  return (
    <section className="panel p-4 my-5">
      <h3 className="font-semibold mb-3">Comparison Mode: {mode === "state" ? "State" : "Department"}</h3>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <select className="w-full rounded-lg border border-slate-300 p-2" value={left} onChange={(e) => setLeft(e.target.value)}>
            {options.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
          <p className="mt-2 text-sm">{left}: <strong>{getCount(left)}</strong> tickets</p>
        </div>
        <div>
          <select className="w-full rounded-lg border border-slate-300 p-2" value={right} onChange={(e) => setRight(e.target.value)}>
            {options.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
          <p className="mt-2 text-sm">{right}: <strong>{getCount(right)}</strong> tickets</p>
        </div>
      </div>
    </section>
  );
}
