"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listReviewedZorgmomenten, listOpenAlerts } from "@/lib/api";
import { Loader2, AlertCircle, AlertTriangle, ClipboardList, ChevronRight } from "lucide-react";

const ALERT_LABELS: Record<string, string> = {
  care_deviation: "Afwijking van planning",
  mood_change: "Verandering in stemming",
  behaviour_change: "Verandering in gedrag",
};

export default function DashboardPage() {
  const [zorgmomenten, setZorgmomenten] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([listReviewedZorgmomenten(), listOpenAlerts()])
      .then(([zm, al]) => {
        setZorgmomenten(zm);
        setAlerts(al);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Kon overzicht niet laden."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="max-w-3xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-slate-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Laden…</p>
      </main>
    );
  }
  if (error) {
    return (
      <main className="max-w-3xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh]">
        <AlertCircle className="text-red-500" size={28} />
        <p className="text-red-700 text-sm">{error}</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-6 pt-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1">Teamoverzicht</h1>
      <p className="text-sm text-slate-500 mb-6">Alleen door zorgmedewerkers gecontroleerde en opgeslagen zorgmomenten.</p>

      {alerts.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <AlertTriangle size={13} />
            Open aandachtspunten
          </h2>
          <ul className="space-y-2">
            {alerts.map((a) => (
              <li
                key={a.id}
                className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex items-start gap-2.5"
              >
                <AlertTriangle size={16} className="text-amber-500 mt-0.5 shrink-0" />
                <div>
                  <span className="font-medium text-sm text-amber-900">{ALERT_LABELS[a.alert_type] ?? a.alert_type}</span>
                  <p className="text-sm text-amber-800/80">{a.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Zorgmomenten</h2>
        {zorgmomenten.length === 0 ? (
          <div className="bg-white border border-dashed border-slate-200 rounded-2xl p-10 flex flex-col items-center text-center text-slate-400">
            <ClipboardList size={28} />
            <p className="text-sm mt-2">Nog geen opgeslagen zorgmomenten.</p>
          </div>
        ) : (
          <ul className="space-y-2">
            {zorgmomenten.map((zm) => (
              <li key={zm.id}>
                <Link
                  href={`/dashboard/${zm.id}`}
                  className="flex items-center justify-between gap-3 bg-white border border-slate-200 rounded-xl p-4 hover:border-teal-300 hover:shadow-sm transition-all"
                >
                  <span className="text-sm text-slate-700">
                    {zm.actual_care_summary?.slice(0, 90) ?? "(geen samenvatting)"}
                  </span>
                  <ChevronRight size={16} className="text-slate-300 shrink-0" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
