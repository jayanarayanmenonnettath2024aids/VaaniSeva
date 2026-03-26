import { AppShell } from "../../components/AppShell";
import { DrilldownMap } from "../../components/DrilldownMap";
import { InsightPanel } from "../../components/InsightPanel";

export function DepartmentHeatmap() {
  return (
    <AppShell title="Department Heatmap" subtitle="Department-specific hotspots and regional drill-down analysis.">
      <DrilldownMap />
      <InsightPanel />
    </AppShell>
  );
}
