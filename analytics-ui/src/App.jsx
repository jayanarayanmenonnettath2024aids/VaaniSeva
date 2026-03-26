import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

const AdminCommandCenter = lazy(() => import("./pages/admin/AdminCommandCenter").then((m) => ({ default: m.AdminCommandCenter })));
const AdminGeography = lazy(() => import("./pages/admin/AdminGeography").then((m) => ({ default: m.AdminGeography })));
const AdminIssues = lazy(() => import("./pages/admin/AdminIssues").then((m) => ({ default: m.AdminIssues })));
const AdminSla = lazy(() => import("./pages/admin/AdminSla").then((m) => ({ default: m.AdminSla })));
const AdminPerformance = lazy(() => import("./pages/admin/AdminPerformance").then((m) => ({ default: m.AdminPerformance })));
const DepartmentOverview = lazy(() => import("./pages/department/DepartmentOverview").then((m) => ({ default: m.DepartmentOverview })));
const DepartmentHeatmap = lazy(() => import("./pages/department/DepartmentHeatmap").then((m) => ({ default: m.DepartmentHeatmap })));
const DepartmentTickets = lazy(() => import("./pages/department/DepartmentTickets").then((m) => ({ default: m.DepartmentTickets })));
const DepartmentPerformance = lazy(() => import("./pages/department/DepartmentPerformance").then((m) => ({ default: m.DepartmentPerformance })));
const PublicHeatmap = lazy(() => import("./pages/public/PublicHeatmap").then((m) => ({ default: m.PublicHeatmap })));
const PublicExplorer = lazy(() => import("./pages/public/PublicExplorer").then((m) => ({ default: m.PublicExplorer })));
const PublicTrends = lazy(() => import("./pages/public/PublicTrends").then((m) => ({ default: m.PublicTrends })));

function App() {
  return (
    <Suspense fallback={<div className="min-h-screen grid place-items-center text-slate-700">Loading analytics workspace...</div>}>
      <Routes>
        <Route path="/" element={<Navigate to="/admin" replace />} />

        <Route path="/admin" element={<AdminCommandCenter />} />
        <Route path="/admin/geography" element={<AdminGeography />} />
        <Route path="/admin/issues" element={<AdminIssues />} />
        <Route path="/admin/sla" element={<AdminSla />} />
        <Route path="/admin/performance" element={<AdminPerformance />} />

        <Route path="/department" element={<DepartmentOverview />} />
        <Route path="/department/heatmap" element={<DepartmentHeatmap />} />
        <Route path="/department/tickets" element={<DepartmentTickets />} />
        <Route path="/department/performance" element={<DepartmentPerformance />} />

        <Route path="/public" element={<PublicHeatmap />} />
        <Route path="/public/explorer" element={<PublicExplorer />} />
        <Route path="/public/trends" element={<PublicTrends />} />

        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
