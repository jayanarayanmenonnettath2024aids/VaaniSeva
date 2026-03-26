import "leaflet/dist/leaflet.css";

import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";

import { useAnalytics } from "../context/AnalyticsContext";

function aggregatePoints(complaints, regionPath) {
  const keyField = regionPath.state ? (regionPath.district ? "location" : "district") : "state";
  const grouped = {};

  complaints.forEach((item) => {
    const key = item[keyField];
    if (!grouped[key]) {
      grouped[key] = { name: key, count: 0, lat: 0, lng: 0 };
    }
    grouped[key].count += 1;
    grouped[key].lat += item.lat;
    grouped[key].lng += item.lng;
  });

  return Object.values(grouped).map((g) => ({
    ...g,
    lat: g.lat / g.count,
    lng: g.lng / g.count,
  }));
}

export function DrilldownMap() {
  const { filteredComplaints, regionPath, setRegionPath, lastUpdateAt } = useAnalytics();
  const [selectedRegion, setSelectedRegion] = useState(null);

  const points = useMemo(
    () => aggregatePoints(filteredComplaints, regionPath),
    [filteredComplaints, regionPath]
  );

  const center = points[0] ? [points[0].lat, points[0].lng] : [20.5937, 78.9629];

  const onPointClick = (name) => {
    setSelectedRegion(name);
    if (!regionPath.state) {
      setRegionPath((prev) => ({ ...prev, state: name, district: null, locality: null }));
      return;
    }
    if (!regionPath.district) {
      setRegionPath((prev) => ({ ...prev, district: name, locality: null }));
      return;
    }
    setRegionPath((prev) => ({ ...prev, locality: name }));
  };

  const detailRows = useMemo(() => {
    if (!selectedRegion) {
      return [];
    }

    const target = filteredComplaints.filter((item) => {
      if (!regionPath.state) {
        return item.state === selectedRegion;
      }
      if (!regionPath.district) {
        return item.district === selectedRegion;
      }
      return item.location === selectedRegion;
    });

    const issueCount = {};
    target.forEach((item) => {
      issueCount[item.issue_type] = (issueCount[item.issue_type] || 0) + 1;
    });
    const topIssue = Object.entries(issueCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "General";
    const breachPercent = target.length
      ? Math.round((target.filter((item) => item.breached).length / target.length) * 100)
      : 0;

    return {
      total: target.length,
      topIssue,
      breachPercent,
      recent: target.slice(0, 2).map((item) => item.issue),
    };
  }, [selectedRegion, filteredComplaints, regionPath]);

  const isPulsing = Date.now() - lastUpdateAt < 4500;

  const getColor = (count) => {
    if (count >= 100) {
      return "#dc2626";
    }
    if (count >= 50) {
      return "#eab308";
    }
    return "#16a34a";
  };

  return (
    <section className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Geographic Drill-down Heatmap</h3>
        <p className="text-sm text-slate-500">Click bubbles to drill deeper</p>
      </div>

      <div className={`h-[340px] rounded-xl overflow-hidden border border-slate-200 ${isPulsing ? "map-pulse" : ""}`}>
        <MapContainer center={center} zoom={5} className="h-full w-full" scrollWheelZoom>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {points.map((point) => (
            <CircleMarker
              key={point.name}
              center={[point.lat, point.lng]}
              radius={10 + point.count * 2}
              pathOptions={{ color: "#0f766e", fillColor: getColor(point.count), fillOpacity: 0.65 }}
              eventHandlers={{ click: () => onPointClick(point.name) }}
            >
              <Tooltip>
                {point.name}: {point.count} complaints
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div className="grid md:grid-cols-[1fr_1fr] gap-3 mt-3">
        <article className="rounded-xl border border-slate-200 p-3 bg-slate-50 text-sm">
          <p className="font-semibold mb-2">Heatmap Legend</p>
          <p><span className="inline-block w-3 h-3 rounded-full bg-red-600 mr-2" /> High density (100+ complaints)</p>
          <p><span className="inline-block w-3 h-3 rounded-full bg-yellow-500 mr-2" /> Medium (50-100)</p>
          <p><span className="inline-block w-3 h-3 rounded-full bg-green-600 mr-2" /> Low (&lt;50)</p>
        </article>

        <article className="rounded-xl border border-slate-200 p-3 bg-slate-50 text-sm">
          <p className="font-semibold mb-2">Region Drill Panel</p>
          {!selectedRegion ? (
            <p className="text-slate-600">Click a region bubble to view full details.</p>
          ) : (
            <div className="space-y-1">
              <p className="text-base font-semibold">{selectedRegion}</p>
              <p>Total: {detailRows.total} complaints</p>
              <p>Top Issue: {detailRows.topIssue}</p>
              <p>SLA Breach: {detailRows.breachPercent}%</p>
              <p className="font-medium mt-2">Recent Issues:</p>
              {detailRows.recent.map((row, idx) => (
                <p key={idx}>- {row}</p>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
