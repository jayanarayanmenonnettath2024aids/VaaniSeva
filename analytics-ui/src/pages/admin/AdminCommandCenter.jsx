import { AlertsPanel } from "../../components/AlertsPanel";
import { AreaUpdatesPanel } from "../../components/AreaUpdatesPanel";
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
      
      {/* ── Row 1: KPI Cards ───────────────────────────────────────── */}
      <KpiCards />

      {/* ── Row 2: Map (left) + Live Calls + Impact (right) ─────────── */}
      <section className="grid xl:grid-cols-[3fr_2fr] gap-6">
        {/* Left: heatmap */}
        <div className="flex flex-col gap-6">
          <DrilldownMap />
          <ChartsPanel />
        </div>

        {/* Right: stacked panels, all filling height */}
        <div className="flex flex-col gap-6">
          <LiveCallsPanel />
          <AlertsPanel />
          <ImpactPanel />
        </div>
      </section>

      {/* ── Row 3: Area Intelligence + Insight side by side ───────────── */}
      <section className="grid md:grid-cols-2 gap-6">
        <AreaUpdatesPanel />
        <InsightPanel />
      </section>

      {/* ── Row 4: Transcript (full width) ────────────────────────────── */}
      <LiveTranscriptPanel />

    </AppShell>
  );
}
