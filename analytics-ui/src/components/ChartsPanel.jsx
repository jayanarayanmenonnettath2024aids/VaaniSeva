import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAnalytics } from "../context/AnalyticsContext";

const COLORS = ["#0f766e", "#2563eb", "#d97706", "#dc2626", "#7c3aed", "#059669"];

function toDay(ts) {
  return ts.slice(5, 10);
}

export function ChartsPanel() {
  const { filteredComplaints, setIssueType, setDepartment } = useAnalytics();

  const trendMap = {};
  const issueMap = {};
  const deptMap = {};

  filteredComplaints.forEach((c) => {
    const day = toDay(c.created_at);
    trendMap[day] = (trendMap[day] || 0) + 1;
    issueMap[c.issue_type] = (issueMap[c.issue_type] || 0) + 1;
    deptMap[c.department] = (deptMap[c.department] || 0) + 1;
  });

  const trendData = Object.entries(trendMap).map(([day, count]) => ({ day, count }));
  const issueData = Object.entries(issueMap).map(([name, value]) => ({ name, value }));
  const deptData = Object.entries(deptMap).map(([name, value]) => ({ name, value }));

  return (
    <section className="grid grid-cols-1 xl:grid-cols-3 gap-4 my-5">
      <article className="panel p-4">
        <h3 className="font-semibold mb-3">Issue Trend Over Time</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#2563eb" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel p-4">
        <h3 className="font-semibold mb-3">Issue Mix (Click to Filter)</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={issueData}
                dataKey="value"
                nameKey="name"
                outerRadius={85}
                onClick={(entry) => setIssueType(entry.name)}
              >
                {issueData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="panel p-4">
        <h3 className="font-semibold mb-3">Department Load (Click to Filter)</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={deptData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#0f766e" onClick={(entry) => setDepartment(entry.name)} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>
    </section>
  );
}
