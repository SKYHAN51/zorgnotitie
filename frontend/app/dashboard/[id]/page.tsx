"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getZorgmomentDetail } from "@/lib/api";
import { Loader2, AlertCircle, AlertTriangle, CheckCircle2, History } from "lucide-react";

export default function ZorgmomentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getZorgmomentDetail(id)
      .then(setDetail)
      .catch((err) => setError(err instanceof Error ? err.message : "Kon detail niet laden."));
  }, [id]);

  if (error) {
    return (
      <main className="max-w-2xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh]">
        <AlertCircle className="text-red-500" size={28} />
        <p className="text-red-700 text-sm">{error}</p>
      </main>
    );
  }
  if (!detail) {
    return (
      <main className="max-w-2xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-stone-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Laden…</p>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto px-6 pt-12 pb-16">
      <h1 className="text-3xl font-bold tracking-tight text-stone-900 mb-8">Zorgmoment detail</h1>

      <section className="bg-white rounded-3xl shadow-soft p-6 mb-6">
        <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-4 flex items-center gap-1.5">
          <CheckCircle2 size={14} className="text-sage-500" />
          Definitieve, door mens goedgekeurde versie
        </h2>
        <dl className="space-y-4 text-sm">
          <div>
            <dt className="text-stone-400 mb-0.5">Uitgevoerde zorg</dt>
            <dd className="text-stone-700 text-base">{detail.actual_care_summary}</dd>
          </div>
          <div>
            <dt className="text-stone-400 mb-0.5">Afwijking</dt>
            <dd className="text-stone-700 text-base">{detail.deviation_detected ? detail.deviation_reason : "Geen"}</dd>
          </div>
          <div>
            <dt className="text-stone-400 mb-0.5">Stemming</dt>
            <dd className="text-stone-700 text-base">{detail.mood_observation}</dd>
          </div>
          <div>
            <dt className="text-stone-400 mb-0.5">Gedrag</dt>
            <dd className="text-stone-700 text-base">{detail.behaviour_observation}</dd>
          </div>
        </dl>
        <p className="text-xs text-stone-400 mt-5 pt-4 border-t border-stone-100">
          Beoordeeld door: {detail.reviewed_by}
        </p>
      </section>

      <section className="bg-white rounded-3xl shadow-soft p-6 mb-6">
        <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-4 flex items-center gap-1.5">
          <AlertTriangle size={14} className="text-amber-500" />
          Aandachtspunten
        </h2>
        {detail.alerts?.length ? (
          <ul className="space-y-2.5">
            {detail.alerts.map((a: any) => (
              <li key={a.id} className="text-sm text-amber-900 bg-amber-50 rounded-xl p-3">
                <span className="font-medium">{a.alert_type}</span>: {a.reason}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-stone-400">Geen aandachtspunten.</p>
        )}
      </section>

      <section className="bg-white rounded-3xl shadow-soft p-6">
        <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wide mb-4 flex items-center gap-1.5">
          <History size={14} />
          Audit — AI-voorstel vs. definitieve versie
        </h2>
        {detail.audit_log?.map((entry: any) => (
          <div key={entry.id} className="bg-cream-50 rounded-2xl p-4 mb-2.5 text-sm last:mb-0">
            <p className="font-medium mb-1.5 text-stone-500 text-xs uppercase tracking-wide">AI-voorstel</p>
            <pre className="bg-white rounded-xl p-3 overflow-x-auto text-xs">{JSON.stringify(entry.before_json, null, 2)}</pre>
            <p className="font-medium mb-1.5 mt-3 text-stone-500 text-xs uppercase tracking-wide">Definitieve versie (mens)</p>
            <pre className="bg-white rounded-xl p-3 overflow-x-auto text-xs">{JSON.stringify(entry.after_json, null, 2)}</pre>
          </div>
        ))}
      </section>
    </main>
  );
}
