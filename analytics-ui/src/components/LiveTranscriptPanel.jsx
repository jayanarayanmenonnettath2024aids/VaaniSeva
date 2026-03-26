import { useAnalytics } from "../context/AnalyticsContext";

export function LiveTranscriptPanel() {
  const { liveTranscript } = useAnalytics();

  return (
    <section className="panel p-4">
      <h3 className="text-lg font-semibold mb-2">Live Transcript</h3>
      <p className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
        "{liveTranscript}"
      </p>
    </section>
  );
}
