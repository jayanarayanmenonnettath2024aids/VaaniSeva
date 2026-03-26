import { createContext, useContext, useMemo, useState } from "react";

import { complaints as seedComplaints } from "../data/mockData";

const AnalyticsContext = createContext(null);

function isWithinRange(createdAt, range) {
  const now = new Date("2026-03-26T12:00:00Z").getTime();
  const ts = new Date(createdAt).getTime();
  const hours = range === "24h" ? 24 : range === "7d" ? 24 * 7 : 24 * 30;
  return now - ts <= hours * 60 * 60 * 1000;
}

export function AnalyticsProvider({ children }) {
  const [complaints, setComplaints] = useState(seedComplaints);
  const [dateRange, setDateRangeState] = useState("7d");
  const [issueType, setIssueType] = useState("All");
  const [department, setDepartment] = useState("All");
  const [regionPath, setRegionPath] = useState({ country: "India", state: null, district: null, locality: null });
  const [lastUpdateAt, setLastUpdateAt] = useState(Date.now());
  const [demoScriptRunning, setDemoScriptRunning] = useState(false);
  const [demoStepMessage, setDemoStepMessage] = useState("Ready");
  const [liveTranscript, setLiveTranscript] = useState("There is a pothole near my house in Anna Nagar.");
  const [impactStatement, setImpactStatement] = useState(
    "This system can reduce grievance resolution delays by 40%."
  );
  const [systemStatus] = useState({
    aiEngine: "Active",
    callSystem: "Connected",
    slaMonitor: "Running",
  });
  const [liveCalls, setLiveCalls] = useState([
    {
      id: "call-live-1",
      caller: "Ravi Kumar",
      language: "Tamil",
      issue: "Road pothole",
      status: "Processing...",
    },
  ]);

  const playNotification = () => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.22);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.22);
    } catch (err) {
      // Audio is optional for demo mode.
      console.debug("Audio unavailable", err);
    }
  };

  const setDateRange = (nextRange) => {
    setDateRangeState(nextRange);
    setLastUpdateAt(Date.now());
  };

  const createDemoComplaint = (overrides = {}) => {
    const now = new Date();
    return {
      id: `TKT-${Math.floor(100000 + Math.random() * 899999)}`,
      issue_type: "Garbage",
      issue: "Garbage complaints increased near market area",
      department: "Sanitation",
      status: "assigned",
      priority: "low",
      location: "Town Hall",
      district: "Coimbatore",
      state: "Tamil Nadu",
      country: "India",
      lat: 11.0168,
      lng: 76.9558,
      created_at: now.toISOString(),
      resolved_at: null,
      sla_hours: 24,
      breached: false,
      ...overrides,
    };
  };

  const startDemoMode = () => {
    const newComplaint = createDemoComplaint();

    setComplaints((prev) => [newComplaint, ...prev]);
    setLiveCalls((prev) => [
      {
        id: `call-${Date.now()}`,
        caller: "Ravi Kumar",
        language: "Tamil",
        issue: "Road pothole",
        status: "Ticket created",
      },
      ...prev.slice(0, 2),
    ]);
    setLastUpdateAt(Date.now());
    playNotification();
  };

  const runFullSystemDemo = async () => {
    if (demoScriptRunning) {
      return;
    }

    const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const stepDelay = 1700;

    setDemoScriptRunning(true);
    setDemoStepMessage("Step 1 - Incoming call...");
    setLiveCalls((prev) => [
      {
        id: `call-${Date.now()}`,
        caller: "Ravi Kumar",
        language: "Tamil",
        issue: "Road pothole",
        status: "Incoming",
      },
      ...prev.slice(0, 2),
    ]);
    await wait(stepDelay);

    setDemoStepMessage("Step 2 - Processing speech...");
    setLiveTranscript("There is a pothole near my house in Anna Nagar, Chennai.");
    await wait(stepDelay);

    setDemoStepMessage("Step 3 - AI detected: Road issue");
    await wait(stepDelay);

    setDemoStepMessage("Step 4 - Ticket created");
    startDemoMode();
    await wait(stepDelay);

    setDemoStepMessage("Step 5 - SMS sent");
    setLiveCalls((prev) => prev.map((call, idx) => (idx === 0 ? { ...call, status: "SMS sent" } : call)));
    await wait(stepDelay);

    setDemoStepMessage("Step 6 - Dashboard updated");
    setLastUpdateAt(Date.now());
    await wait(stepDelay);

    setDemoStepMessage("Step 7 - Heatmap spike");
    const spike = createDemoComplaint({
      issue_type: "Road",
      issue: "Road pothole cluster reported near school zone",
      department: "PWD",
      priority: "medium",
      location: "Anna Nagar",
      district: "Chennai",
      lat: 13.085,
      lng: 80.207,
    });
    setComplaints((prev) => [spike, ...prev]);
    setLastUpdateAt(Date.now());
    playNotification();

    setImpactStatement("This system can reduce grievance resolution delays by 40% with real-time escalation visibility.");
    await wait(500);
    setDemoScriptRunning(false);
  };

  const filteredComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const issueMatch = issueType === "All" || c.issue_type === issueType;
      const deptMatch = department === "All" || c.department === department;
      const rangeMatch = isWithinRange(c.created_at, dateRange);
      const stateMatch = !regionPath.state || c.state === regionPath.state;
      const districtMatch = !regionPath.district || c.district === regionPath.district;
      const localityMatch = !regionPath.locality || c.location === regionPath.locality;
      return issueMatch && deptMatch && rangeMatch && stateMatch && districtMatch && localityMatch;
    });
  }, [complaints, dateRange, issueType, department, regionPath]);

  const summary = useMemo(() => {
    const total = filteredComplaints.length;
    const resolved = filteredComplaints.filter((c) => c.status === "resolved").length;
    const unresolved = total - resolved;
    const breaches = filteredComplaints.filter((c) => c.breached).length;
    return {
      total,
      resolved,
      unresolved,
      breaches,
      resolutionRate: total ? ((resolved / total) * 100).toFixed(1) : "0.0",
    };
  }, [filteredComplaints]);

  const insights = useMemo(() => {
    const issueCount = {};
    const regionCount = {};

    filteredComplaints.forEach((c) => {
      issueCount[c.issue_type] = (issueCount[c.issue_type] || 0) + 1;
      regionCount[c.district] = (regionCount[c.district] || 0) + 1;
    });

    const topIssue = Object.entries(issueCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "General";
    const topRegion = Object.entries(regionCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "No region";

    const now = new Date("2026-03-26T12:00:00Z").getTime();
    const weekMs = 7 * 24 * 60 * 60 * 1000;
    const currentWeek = complaints.filter((c) => now - new Date(c.created_at).getTime() <= weekMs);
    const previousWeek = complaints.filter((c) => {
      const diff = now - new Date(c.created_at).getTime();
      return diff > weekMs && diff <= weekMs * 2;
    });

    const currentGarbage = currentWeek.filter((c) => c.issue_type === "Garbage" && c.district === "Coimbatore").length;
    const previousGarbage = previousWeek.filter((c) => c.issue_type === "Garbage" && c.district === "Coimbatore").length;
    const growth = previousGarbage === 0 ? currentGarbage * 100 : Math.round(((currentGarbage - previousGarbage) / previousGarbage) * 100);

    const resolvedByDistrict = {};
    complaints.forEach((c) => {
      if (!c.resolved_at) {
        return;
      }
      const created = new Date(c.created_at).getTime();
      const resolved = new Date(c.resolved_at).getTime();
      const hours = (resolved - created) / (1000 * 60 * 60);
      if (!resolvedByDistrict[c.district]) {
        resolvedByDistrict[c.district] = [];
      }
      resolvedByDistrict[c.district].push(hours);
    });

    let fastestDistrict = "Bengaluru Urban";
    let fastestAvg = Number.POSITIVE_INFINITY;
    Object.entries(resolvedByDistrict).forEach(([district, values]) => {
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      if (avg < fastestAvg) {
        fastestAvg = avg;
        fastestDistrict = district;
      }
    });

    return {
      topIssue,
      topRegion,
      narrative: `Most affected region is ${topRegion}; ${topIssue} is the fastest growing issue in selected filters.`,
      autoLines: [
        `Garbage complaints increased ${Math.max(growth, 0)}% in Coimbatore this week.`,
        `Electricity issues resolved fastest in ${fastestDistrict}.`,
      ],
    };
  }, [filteredComplaints, complaints]);

  const value = {
    complaints,
    setComplaints,
    filteredComplaints,
    dateRange,
    setDateRange,
    issueType,
    setIssueType,
    department,
    setDepartment,
    regionPath,
    setRegionPath,
    summary,
    insights,
    liveCalls,
    liveTranscript,
    impactStatement,
    systemStatus,
    startDemoMode,
    runFullSystemDemo,
    demoScriptRunning,
    demoStepMessage,
    lastUpdateAt,
  };

  return <AnalyticsContext.Provider value={value}>{children}</AnalyticsContext.Provider>;
}

export function useAnalytics() {
  const ctx = useContext(AnalyticsContext);
  if (!ctx) {
    throw new Error("useAnalytics must be used inside AnalyticsProvider");
  }
  return ctx;
}
