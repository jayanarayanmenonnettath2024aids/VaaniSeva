import { AlertsPanel } from "../../components/AlertsPanel";
import { AppShell } from "../../components/AppShell";
import { ChartsPanel } from "../../components/ChartsPanel";
import { DrilldownMap } from "../../components/DrilldownMap";
import { ImpactPanel } from "../../components/ImpactPanel";
import { InsightPanel } from "../../components/InsightPanel";
import { KpiCards } from "../../components/KpiCards";
import { LiveCallsPanel } from "../../components/LiveCallsPanel";
import { LiveTranscriptPanel } from "../../components/LiveTranscriptPanel";

export function AdminCommandCenter() {
  return (
    <AppShell title="Command Center" subtitle="National command view with live KPIs, alerts, and drill-down heatmap.">
      <KpiCards />
      <section className="grid xl:grid-cols-[2fr_1fr] gap-4">
        <DrilldownMap />
        <div className="space-y-4">
          <LiveCallsPanel />
          <LiveTranscriptPanel />
          <ImpactPanel />
          <AlertsPanel />
        </div>
      </section>
      <ChartsPanel />
      <InsightPanel />
    </AppShell>
  );
}
