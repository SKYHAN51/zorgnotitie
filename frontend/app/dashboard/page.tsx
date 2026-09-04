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
      <main className="max-w-3xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-stone-400 min-h-[60vh]">
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
    <main className="max-w-3xl mx-auto px-6 pt-12 pb-16">
      <h1 className="text-3xl font-bold tracking-tight text-stone-900 mb-1.5">Teamoverzicht</h1>
      <p className="text-stone-500 mb-8">Alleen door zorgmedewerkers gecontroleerde en opgeslagen zorgmomenten.</p>

      {alerts.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <AlertTriangle size={13} />
            Open aandachtspunten
          </h2>
          <ul className="space-y-2.5">
            {alerts.map((a) => (
              <li
                key={a.id}
                className="bg-amber-50 rounded-2xl p-4 flex items-start gap-3"
              >
                <AlertTriangle size={18} className="text-amber-500 mt-0.5 shrink-0" />
                <div>
                  <span className="font-medium text-sm text-amber-900">{ALERT_LABELS[a.alert_type] ?? a.alert_type}</span>
                  <p className="text-sm text-amber-800/80 mt-0.5">{a.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-3">Zorgmomenten</h2>
        {zorgmomenten.length === 0 ? (
          <div className="bg-white rounded-3xl shadow-softer p-12 flex flex-col items-center text-center text-stone-400">
            <ClipboardList size={30} />
            <p className="text-sm mt-3">Nog geen opgeslagen zorgmomenten.</p>
          </div>
        ) : (
          <ul className="space-y-2.5">
            {zorgmomenten.map((zm) => (
              <li key={zm.id}>
                <Link
                  href={`/dashboard/${zm.id}`}
                  className="flex items-center justify-between gap-3 bg-white rounded-2xl p-5 shadow-softer hover:shadow-soft hover:-translate-y-0.5 transition-all"
                >
                  <span className="text-sm text-stone-700">
                    {zm.actual_care_summary?.slice(0, 90) ?? "(geen samenvatting)"}
                  </span>
                  <ChevronRight size={16} className="text-sage-500 shrink-0" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
