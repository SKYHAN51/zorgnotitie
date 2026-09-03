"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listReviewedZorgmomenten, listOpenAlerts } from "@/lib/api";

const ALERT_LABELS: Record<string, string> = {
  care_deviation: "Afwijking van planning",
  mood_change: "Verandering in stemming",
  behaviour_change: "Verandering in gedrag",
};

export default function DashboardPage() {
  const [zorgmomenten, setZorgmomenten] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listReviewedZorgmomenten(), listOpenAlerts()])
      .then(([zm, al]) => {
        setZorgmomenten(zm);
        setAlerts(al);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <main className="max-w-3xl mx-auto p-6">Laden…</main>;

  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Teamoverzicht</h1>

      {alerts.length > 0 && (
        <section className="mb-6">
          <h2 className="text-lg font-medium mb-2">Open aandachtspunten</h2>
          <ul className="space-y-2">
            {alerts.map((a) => (
              <li key={a.id} className="bg-amber-50 border border-amber-200 rounded p-3">
                <span className="font-medium">{ALERT_LABELS[a.alert_type] ?? a.alert_type}</span>
                {" — "}
                <span className="text-sm text-slate-700">{a.reason}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="text-lg font-medium mb-2">Zorgmomenten</h2>
        <ul className="space-y-2">
          {zorgmomenten.map((zm) => (
            <li key={zm.id} className="border rounded p-3">
              <Link href={`/dashboard/${zm.id}`} className="underline">
                {zm.actual_care_summary?.slice(0, 80) ?? "(geen samenvatting)"}
              </Link>
            </li>
          ))}
          {zorgmomenten.length === 0 && <p className="text-slate-500">Nog geen opgeslagen zorgmomenten.</p>}
        </ul>
      </section>
    </main>
  );
}
