import { useAnalytics } from "../context/AnalyticsContext";
import { useState, useEffect, useRef } from "react";

export function NewTicketAlert() {
  const { complaints } = useAnalytics();
  const [showAlert, setShowAlert] = useState(false);
  const [latestTicket, setLatestTicket] = useState(null);
  const prevLengthRef = useRef(complaints.length);

  useEffect(() => {
    const newLength = complaints.length;
    const prevLength = prevLengthRef.current;

    // When new complaint is added (length increased)
    if (newLength > prevLength && complaints[0]) {
      setLatestTicket(complaints[0]);
      setShowAlert(true);

      // Auto-dismiss after 4 seconds
      const timer = setTimeout(() => {
        setShowAlert(false);
      }, 4000);

      return () => clearTimeout(timer);
    }

    prevLengthRef.current = newLength;
  }, [complaints]);

  if (!showAlert || !latestTicket) return null;

  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 pointer-events-auto animate-slide-in">
      <div className="rounded-lg border-2 border-red-500 bg-red-50 px-6 py-3 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="text-2xl animate-pulse">🔴</div>
            <span className="font-bold text-red-700">NEW COMPLAINT RECEIVED</span>
          </div>
          <div className="h-12 w-px bg-red-300"></div>
          <div className="text-sm text-slate-700">
            <p className="font-medium">{latestTicket.id}</p>
            <p className="text-xs text-slate-600">{latestTicket.issue_type} • {latestTicket.district}</p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translate(-50%, -20px);
          }
          to {
            opacity: 1;
            transform: translate(-50%, 0);
          }
        }
        
        .animate-slide-in {
          animation: slideIn 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}
