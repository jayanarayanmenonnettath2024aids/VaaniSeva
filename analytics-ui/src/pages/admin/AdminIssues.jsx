import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { InsightPanel } from "../../components/InsightPanel";
import { TicketTable } from "../../components/TicketTable";

export function AdminIssues() {
  return (
    <AppShell title="Issue Intelligence" subtitle="Issue trends, growth detection, and emerging complaint behavior.">
      <ChartsPanel />
      <InsightPanel />
      <TicketTable compact />
    </AppShell>
  );
}
