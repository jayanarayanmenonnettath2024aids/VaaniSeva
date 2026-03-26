import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { ComparisonPanel } from "../../components/ComparisonPanel";
import { KpiCards } from "../../components/KpiCards";
import { TicketTable } from "../../components/TicketTable";

export function AdminPerformance() {
  return (
    <AppShell title="Performance Analytics" subtitle="Resolution rate, department comparison, and average resolution behavior.">
      <KpiCards />
      <ChartsPanel />
      <ComparisonPanel mode="department" />
      <TicketTable compact />
    </AppShell>
  );
}
