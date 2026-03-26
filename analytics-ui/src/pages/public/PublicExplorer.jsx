import { AppShell } from "../../components/AppShell";
import { DrilldownMap } from "../../components/DrilldownMap";
import { TicketTable } from "../../components/TicketTable";

export function PublicExplorer() {
  return (
    <AppShell title="City / Region Explorer" subtitle="Explore a region and instantly inspect issue summaries and ticket slices.">
      <DrilldownMap />
      <TicketTable compact />
    </AppShell>
  );
}
