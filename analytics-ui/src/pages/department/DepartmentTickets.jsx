import { AppShell } from "../../components/AppShell";
import { TicketTable } from "../../components/TicketTable";

export function DepartmentTickets() {
  return (
    <AppShell title="Ticket Operations Panel" subtitle="Full ticket operations table with filter-aware cross interactions.">
      <TicketTable />
    </AppShell>
  );
}
