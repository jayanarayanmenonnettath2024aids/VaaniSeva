import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { KpiCards } from "../../components/KpiCards";

export function DepartmentOverview() {
  return (
    <AppShell title="Department Overview" subtitle="Department KPI cockpit for operational planning and workload management.">
      <KpiCards />
      <ChartsPanel />
    </AppShell>
  );
}
