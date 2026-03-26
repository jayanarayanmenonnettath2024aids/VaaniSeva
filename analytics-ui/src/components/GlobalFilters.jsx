import { departments, dateRanges, issueTypes } from "../data/mockData";
import { useAnalytics } from "../context/AnalyticsContext";

export function GlobalFilters() {
  const {
    dateRange,
    setDateRange,
    issueType,
    setIssueType,
    department,
    setDepartment,
    regionPath,
    setRegionPath,
  } = useAnalytics();

  return (
    <section className="panel p-4 mb-5">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <div className="text-sm">
          <span className="block text-slate-600 mb-1">Time filter</span>
          <div className="inline-flex rounded-lg border border-slate-300 overflow-hidden">
            {dateRanges.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setDateRange(item)}
                className={`px-3 py-2 text-sm ${
                  dateRange === item ? "bg-slate-900 text-white" : "bg-white text-slate-700"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <label className="text-sm">
          <span className="block text-slate-600 mb-1">Issue type</span>
          <select
            value={issueType}
            onChange={(e) => setIssueType(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            {issueTypes.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>

        <label className="text-sm">
          <span className="block text-slate-600 mb-1">Department</span>
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            {departments.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={() => setRegionPath({ country: "India", state: null, district: null, locality: null })}
          className="rounded-lg bg-slate-900 text-white px-4 py-2 self-end"
        >
          Reset Drill-down
        </button>
      </div>
      <p className="mt-3 text-sm text-slate-600">
        Scope: {regionPath.country}
        {regionPath.state ? ` / ${regionPath.state}` : ""}
        {regionPath.district ? ` / ${regionPath.district}` : ""}
        {regionPath.locality ? ` / ${regionPath.locality}` : ""}
      </p>
    </section>
  );
}
