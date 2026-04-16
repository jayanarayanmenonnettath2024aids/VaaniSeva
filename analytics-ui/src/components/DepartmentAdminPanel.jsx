import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function authHeaders() {
  const token = sessionStorage.getItem("vaaniseva_token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token || ""}`,
  };
}

export function DepartmentAdminPanel() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    city_id: "coimbatore",
    issue_type: "Road",
    sla_hours: 24,
    contact_email: "",
  });

  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  }, [rows]);

  const loadDepartments = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/departments`, { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Failed to load departments");
        return;
      }
      setRows(Array.isArray(data.departments) ? data.departments : []);
    } catch {
      setError("Failed to load departments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  const createDepartment = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API_BASE}/departments`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          ...form,
          sla_hours: Number(form.sla_hours || 24),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Failed to create department");
        return;
      }
      setForm({ name: "", city_id: "coimbatore", issue_type: "Road", sla_hours: 24, contact_email: "" });
      await loadDepartments();
    } catch {
      setError("Failed to create department");
    }
  };

  const updateDepartment = async (departmentId, updates) => {
    try {
      const res = await fetch(`${API_BASE}/departments/${departmentId}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Failed to update department");
        return;
      }
      await loadDepartments();
    } catch {
      setError("Failed to update department");
    }
  };

  const deleteDepartment = async (departmentId) => {
    try {
      const res = await fetch(`${API_BASE}/departments/${departmentId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Failed to delete department");
        return;
      }
      await loadDepartments();
    } catch {
      setError("Failed to delete department");
    }
  };

  return (
    <section className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">Department Management</h3>
        <button
          type="button"
          onClick={loadDepartments}
          className="text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {error ? <p className="text-sm text-rose-600 mb-3">{error}</p> : null}

      <form onSubmit={createDepartment} className="grid md:grid-cols-5 gap-2 mb-4">
        <input
          className="input"
          placeholder="Department"
          value={form.name}
          onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
          required
        />
        <input
          className="input"
          placeholder="Issue Type"
          value={form.issue_type}
          onChange={(e) => setForm((p) => ({ ...p, issue_type: e.target.value }))}
          required
        />
        <input
          className="input"
          type="number"
          min="1"
          placeholder="SLA Hours"
          value={form.sla_hours}
          onChange={(e) => setForm((p) => ({ ...p, sla_hours: e.target.value }))}
          required
        />
        <input
          className="input"
          type="email"
          placeholder="Contact Email"
          value={form.contact_email}
          onChange={(e) => setForm((p) => ({ ...p, contact_email: e.target.value }))}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white rounded-lg px-3 py-2 text-sm font-bold hover:bg-blue-700"
        >
          Add
        </button>
      </form>

      <div className="space-y-2">
        {loading ? <p className="text-sm text-slate-500">Loading departments...</p> : null}
        {!loading && sorted.length === 0 ? <p className="text-sm text-slate-500">No departments found.</p> : null}

        {sorted.map((d) => (
          <div key={d.department_id || d.name} className="rounded-lg border border-slate-200 p-3">
            <div className="flex flex-wrap items-center gap-2 justify-between">
              <div>
                <p className="font-semibold text-slate-900">{d.name}</p>
                <p className="text-xs text-slate-500">
                  {d.issue_type || "General"} | SLA: {d.sla_hours || 24}h | {d.contact_email || "no-contact"}
                </p>
              </div>
              {d.department_id ? (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const next = prompt("Update SLA hours", String(d.sla_hours || 24));
                      if (!next) return;
                      updateDepartment(d.department_id, { sla_hours: Number(next) });
                    }}
                    className="text-xs font-bold px-2.5 py-1.5 rounded-md border border-slate-300 hover:bg-slate-50"
                  >
                    Update SLA
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteDepartment(d.department_id)}
                    className="text-xs font-bold px-2.5 py-1.5 rounded-md border border-rose-300 text-rose-700 hover:bg-rose-50"
                  >
                    Delete
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
