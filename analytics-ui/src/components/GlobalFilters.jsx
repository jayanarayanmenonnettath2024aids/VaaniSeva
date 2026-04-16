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

  const resetAll = () => {
    setIssueType("All");
    setDepartment("All");
    setDateRange("7d");
    setRegionPath({ country: "India", state: null, district: null, locality: null });
  };

  /* Build breadcrumb segments */
  const crumbs = [regionPath.country, regionPath.state, regionPath.district, regionPath.locality].filter(Boolean);

  return (
    <section className="panel p-5">
      <div className="flex flex-col lg:flex-row lg:items-end gap-5">

        {/* Time Filter */}
        <div className="flex-shrink-0">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Time Range</p>
          <div className="inline-flex rounded-xl overflow-hidden border border-slate-200 shadow-sm">
            {dateRanges.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setDateRange(item)}
                className={`px-4 py-2.5 text-[11px] font-bold uppercase tracking-wider transition-all ${
                  dateRange === item
                    ? "bg-blue-600 text-white shadow-inner"
                    : "bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {/* Issue Type */}
        <div className="flex-1 min-w-[160px]">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Issue Type</p>
          <div className="relative">
            <select
              value={issueType}
              onChange={(e) => setIssueType(e.target.value)}
              className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 py-2.5 pr-10 text-sm font-semibold text-slate-800 shadow-sm hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
            >
              {issueTypes.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </div>
        </div>

        {/* Department */}
        <div className="flex-1 min-w-[160px]">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Department</p>
          <div className="relative">
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full appearance-none rounded-xl border border-slate-200 bg-white px-4 py-2.5 pr-10 text-sm font-semibold text-slate-800 shadow-sm hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
            >
              {departments.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </div>
        </div>

        {/* Reset Button */}
        <button
          type="button"
          onClick={resetAll}
          className="flex-shrink-0 group inline-flex items-center gap-2 bg-slate-900 hover:bg-blue-600 text-white font-black text-[10px] uppercase tracking-widest px-6 py-3 rounded-xl shadow-lg shadow-slate-900/20 hover:shadow-blue-600/30 transition-all hover:-translate-y-0.5"
        >
          <svg className="w-3.5 h-3.5 group-hover:rotate-180 transition-transform duration-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>
          </svg>
          Reset All
        </button>
      </div>

      {/* Breadcrumb scope */}
      <div className="mt-4 flex items-center gap-1.5 flex-wrap">
        <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest mr-1">📍 Scope:</span>
        {crumbs.map((c, i) => (
          <span key={i} className="flex items-center gap-1.5">
            {i > 0 && <span className="text-slate-300 text-[10px]">→</span>}
            <button
              type="button"
              onClick={() => {
                const keys = ["country", "state", "district", "locality"];
                const next = { country: "India", state: null, district: null, locality: null };
                for (let j = 1; j <= i; j++) next[keys[j]] = crumbs[j];
                setRegionPath(next);
              }}
              className={`text-[11px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                i === crumbs.length - 1
                  ? "bg-blue-100 text-blue-700 border border-blue-200"
                  : "text-slate-500 hover:text-blue-600 hover:bg-blue-50"
              }`}
            >
              {c}
            </button>
          </span>
        ))}
        {crumbs.length > 1 && (
          <button
            type="button"
            onClick={() => setRegionPath({ country: "India", state: null, district: null, locality: null })}
            className="ml-2 text-[9px] font-black text-rose-500 hover:text-rose-700 uppercase tracking-widest transition-colors"
          >
            × Clear
          </button>
        )}
      </div>
    </section>
  );
}
