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
      <main className="max-w-2xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-slate-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Laden…</p>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto p-6 pt-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-6">Zorgmoment detail</h1>

      <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 mb-5">
        <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <CheckCircle2 size={13} className="text-emerald-500" />
          Definitieve, door mens goedgekeurde versie
        </h2>
        <dl className="space-y-3 text-sm">
          <div>
            <dt className="text-slate-400">Uitgevoerde zorg</dt>
            <dd className="text-slate-700">{detail.actual_care_summary}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Afwijking</dt>
            <dd className="text-slate-700">{detail.deviation_detected ? detail.deviation_reason : "Geen"}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Stemming</dt>
            <dd className="text-slate-700">{detail.mood_observation}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Gedrag</dt>
            <dd className="text-slate-700">{detail.behaviour_observation}</dd>
          </div>
        </dl>
        <p className="text-xs text-slate-400 mt-4 pt-3 border-t border-slate-100">
          Beoordeeld door: {detail.reviewed_by}
        </p>
      </section>

      <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 mb-5">
        <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <AlertTriangle size={13} className="text-amber-500" />
          Aandachtspunten
        </h2>
        {detail.alerts?.length ? (
          <ul className="space-y-2">
            {detail.alerts.map((a: any) => (
              <li key={a.id} className="text-sm text-slate-700 bg-amber-50 border border-amber-200 rounded-lg p-2.5">
                <span className="font-medium">{a.alert_type}</span>: {a.reason}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-400">Geen aandachtspunten.</p>
        )}
      </section>

      <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5">
        <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <History size={13} />
          Audit — AI-voorstel vs. definitieve versie
        </h2>
        {detail.audit_log?.map((entry: any) => (
          <div key={entry.id} className="border border-slate-200 rounded-xl p-3 mb-2 text-sm last:mb-0">
            <p className="font-medium mb-1 text-slate-600 text-xs uppercase tracking-wide">AI-voorstel</p>
            <pre className="bg-slate-50 p-2 rounded-lg overflow-x-auto text-xs">{JSON.stringify(entry.before_json, null, 2)}</pre>
            <p className="font-medium mb-1 mt-3 text-slate-600 text-xs uppercase tracking-wide">Definitieve versie (mens)</p>
            <pre className="bg-slate-50 p-2 rounded-lg overflow-x-auto text-xs">{JSON.stringify(entry.after_json, null, 2)}</pre>
          </div>
        ))}
      </section>
    </main>
  );
}
