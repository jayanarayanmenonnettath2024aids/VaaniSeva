import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { InsightPanel } from "../../components/InsightPanel";

export function PublicTrends() {
  return (
    <AppShell title="Public Insights & Trends" subtitle="Most common complaint patterns and trend storytelling for citizens.">
      <ChartsPanel />
      <InsightPanel />
    </AppShell>
  );
}
