import { AppShell } from "../../components/AppShell";
import { DrilldownMap } from "../../components/DrilldownMap";

export function PublicHeatmap() {
  return (
    <AppShell title="Public Heatmap" subtitle="Public-facing issue density map with transparent region drill-down.">
      <DrilldownMap />
    </AppShell>
  );
}
