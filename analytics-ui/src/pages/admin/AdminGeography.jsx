import { AppShell } from "../../components/AppShell";
import { ComparisonPanel } from "../../components/ComparisonPanel";
import { DrilldownMap } from "../../components/DrilldownMap";
import { TicketTable } from "../../components/TicketTable";

export function AdminGeography() {
  return (
    <AppShell title="Geographic Intelligence" subtitle="India to state to district drill-down with clustering and region comparisons.">
      <DrilldownMap />
      <ComparisonPanel mode="state" />
      <TicketTable compact />
    </AppShell>
  );
}
