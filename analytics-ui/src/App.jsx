import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import { AnalyticsProvider } from "./context/AnalyticsContext";
import { ProtectedRoute } from "./components/ProtectedRoute";

// Public pages
const LandingPage = lazy(() => import("./pages/LandingPage").then((m) => ({ default: m.LandingPage })));
const LoginPage   = lazy(() => import("./pages/LoginPage").then((m) => ({ default: m.LoginPage })));

// Admin pages
const AdminCommandCenter  = lazy(() => import("./pages/admin/AdminCommandCenter").then((m) => ({ default: m.AdminCommandCenter })));
const AdminGeography      = lazy(() => import("./pages/admin/AdminGeography").then((m) => ({ default: m.AdminGeography })));
const AdminIssues         = lazy(() => import("./pages/admin/AdminIssues").then((m) => ({ default: m.AdminIssues })));
const AdminSla            = lazy(() => import("./pages/admin/AdminSla").then((m) => ({ default: m.AdminSla })));
const AdminPerformance    = lazy(() => import("./pages/admin/AdminPerformance").then((m) => ({ default: m.AdminPerformance })));

// Department pages
const DepartmentOverview    = lazy(() => import("./pages/department/DepartmentOverview").then((m) => ({ default: m.DepartmentOverview })));
const DepartmentHeatmap     = lazy(() => import("./pages/department/DepartmentHeatmap").then((m) => ({ default: m.DepartmentHeatmap })));
const DepartmentTickets     = lazy(() => import("./pages/department/DepartmentTickets").then((m) => ({ default: m.DepartmentTickets })));
const DepartmentPerformance = lazy(() => import("./pages/department/DepartmentPerformance").then((m) => ({ default: m.DepartmentPerformance })));

const Loading = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50">
    <div className="text-center">
      <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-black text-white text-lg mx-auto mb-4 animate-pulse">V</div>
      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Loading VaaniSeva...</p>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <AnalyticsProvider>
        <Suspense fallback={<Loading />}>
          <Routes>
            {/* ── Public ───────────────────────────────────────── */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />

            {/* ── Admin (requires role: admin) ──────────────────── */}
            <Route path="/admin" element={
              <ProtectedRoute requiredRole="admin"><AdminCommandCenter /></ProtectedRoute>
            } />
            <Route path="/admin/geography" element={
              <ProtectedRoute requiredRole="admin"><AdminGeography /></ProtectedRoute>
            } />
            <Route path="/admin/issues" element={
              <ProtectedRoute requiredRole="admin"><AdminIssues /></ProtectedRoute>
            } />
            <Route path="/admin/sla" element={
              <ProtectedRoute requiredRole="admin"><AdminSla /></ProtectedRoute>
            } />
            <Route path="/admin/performance" element={
              <ProtectedRoute requiredRole="admin"><AdminPerformance /></ProtectedRoute>
            } />

            {/* ── Department (requires role: department) ─────────── */}
            <Route path="/department" element={
              <ProtectedRoute requiredRole="department"><DepartmentOverview /></ProtectedRoute>
            } />
            <Route path="/department/heatmap" element={
              <ProtectedRoute requiredRole="department"><DepartmentHeatmap /></ProtectedRoute>
            } />
            <Route path="/department/tickets" element={
              <ProtectedRoute requiredRole="department"><DepartmentTickets /></ProtectedRoute>
            } />
            <Route path="/department/performance" element={
              <ProtectedRoute requiredRole="department"><DepartmentPerformance /></ProtectedRoute>
            } />

            {/* ── Fallback ──────────────────────────────────────── */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AnalyticsProvider>
    </AuthProvider>
  );
}

export default App;
