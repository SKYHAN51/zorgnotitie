"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getZorgmomentDetail } from "@/lib/api";

export default function ZorgmomentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    getZorgmomentDetail(id).then(setDetail);
  }, [id]);

  if (!detail) return <main className="max-w-2xl mx-auto p-6">Laden…</main>;

  return (
    <main className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Zorgmoment detail</h1>

      <section className="mb-6">
        <h2 className="text-lg font-medium mb-2">Definitieve, door mens goedgekeurde versie</h2>
        <p><strong>Uitgevoerde zorg:</strong> {detail.actual_care_summary}</p>
        <p><strong>Afwijking:</strong> {detail.deviation_detected ? detail.deviation_reason : "Geen"}</p>
        <p><strong>Stemming:</strong> {detail.mood_observation}</p>
        <p><strong>Gedrag:</strong> {detail.behaviour_observation}</p>
        <p className="text-sm text-slate-500 mt-2">Beoordeeld door: {detail.reviewed_by}</p>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-medium mb-2">Aandachtspunten</h2>
        {detail.alerts?.length ? (
          <ul className="space-y-1">
            {detail.alerts.map((a: any) => (
              <li key={a.id}>{a.alert_type}: {a.reason}</li>
            ))}
          </ul>
        ) : (
          <p className="text-slate-500">Geen aandachtspunten.</p>
        )}
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">Audit — AI-voorstel vs. definitieve versie</h2>
        {detail.audit_log?.map((entry: any) => (
          <div key={entry.id} className="border rounded p-3 mb-2 text-sm">
            <p className="font-medium mb-1">AI-voorstel:</p>
            <pre className="bg-slate-50 p-2 rounded overflow-x-auto">{JSON.stringify(entry.before_json, null, 2)}</pre>
            <p className="font-medium mb-1 mt-2">Definitieve versie (mens):</p>
            <pre className="bg-slate-50 p-2 rounded overflow-x-auto">{JSON.stringify(entry.after_json, null, 2)}</pre>
          </div>
        ))}
      </section>
    </main>
  );
}
