import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { ComparisonPanel } from "../../components/ComparisonPanel";

export function DepartmentPerformance() {
  return (
    <AppShell title="Department Performance Tracking" subtitle="SLA performance and backlog trend tracking for department managers.">
      <ChartsPanel />
      <ComparisonPanel mode="department" />
    </AppShell>
  );
}
