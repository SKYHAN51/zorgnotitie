"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { extractZorgmoment, saveZorgmoment, ExtractionDraft } from "@/lib/api";
import { Loader2, AlertCircle, Sparkles, Save } from "lucide-react";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [draft, setDraft] = useState<ExtractionDraft | null>(null);
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    extractZorgmoment(id)
      .then((res) => {
        setDraft(res.extraction_json);
        setTranscript(res.transcript);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  function updateField<K extends keyof ExtractionDraft>(key: K, value: ExtractionDraft[K]) {
    if (!draft) return;
    setDraft({ ...draft, [key]: value });
  }

  async function handleSave() {
    if (!draft) return;
    setSaving(true);
    setError("");
    try {
      await saveZorgmoment(id, draft, "demo-zorgmedewerker");
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Opslaan mislukt.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-stone-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Bezig met concept maken…</p>
      </main>
    );
  }
  if (error && !draft) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh]">
        <AlertCircle className="text-red-500" size={28} />
        <p className="text-red-700 text-sm">{error}</p>
      </main>
    );
  }
  if (!draft) return null;

  return (
    <main className="max-w-xl mx-auto px-6 pt-12 pb-16">
      <h1 className="text-3xl font-bold tracking-tight text-stone-900 mb-1.5">Controleren en opslaan</h1>
      <p className="text-stone-500 flex items-center gap-1.5 mb-8">
        <Sparkles size={15} className="text-sage-500" />
        AI doet een voorstel. Jij controleert en beslist.
      </p>

      <div className="bg-white rounded-3xl shadow-soft p-6 mb-6">
        <span className="block text-xs font-semibold text-stone-400 uppercase tracking-wide mb-2">
          Ruwe transcriptie (audio-opname)
        </span>
        <div className="bg-cream-50 rounded-2xl p-4 text-sm text-stone-600 whitespace-pre-wrap leading-relaxed">
          {transcript || "(geen transcriptie beschikbaar)"}
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-soft p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-stone-600 mb-2">Uitgevoerde zorg</label>
          <textarea
            className="border border-stone-200 rounded-xl p-3.5 w-full text-base bg-cream-50 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-sage-400"
            rows={3}
            value={draft.actual_care_summary}
            onChange={(e) => updateField("actual_care_summary", e.target.value)}
          />
        </div>

        <div className="border-t border-stone-100 pt-6">
          <label className="flex items-center gap-2.5 text-sm text-stone-700">
            <input
              type="checkbox"
              className="w-4 h-4 rounded accent-sage-600"
              checked={draft.deviation_detected}
              onChange={(e) => updateField("deviation_detected", e.target.checked)}
            />
            Afwijking van planning
          </label>
          {draft.deviation_detected && (
            <input
              className="border border-stone-200 rounded-xl p-3 w-full mt-2.5 text-base bg-cream-50 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-sage-400"
              value={draft.deviation_reason ?? ""}
              onChange={(e) => updateField("deviation_reason", e.target.value)}
              placeholder="Reden voor afwijking"
            />
          )}
        </div>

        <div className="border-t border-stone-100 pt-6">
          <label className="block text-sm font-medium text-stone-600 mb-2">Stemming</label>
          <input
            className="border border-stone-200 rounded-xl p-3 w-full text-base bg-cream-50 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-sage-400"
            value={draft.mood_observation}
            onChange={(e) => updateField("mood_observation", e.target.value)}
          />
          <label className="flex items-center gap-2.5 text-sm text-stone-700 mt-2.5">
            <input
              type="checkbox"
              className="w-4 h-4 rounded accent-sage-600"
              checked={draft.mood_changed}
              onChange={(e) => updateField("mood_changed", e.target.checked)}
            />
            Stemming afwijkend van normaal
          </label>
        </div>

        <div className="border-t border-stone-100 pt-6">
          <label className="block text-sm font-medium text-stone-600 mb-2">Gedrag</label>
          <input
            className="border border-stone-200 rounded-xl p-3 w-full text-base bg-cream-50 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-sage-400"
            value={draft.behaviour_observation}
            onChange={(e) => updateField("behaviour_observation", e.target.value)}
          />
          <label className="flex items-center gap-2.5 text-sm text-stone-700 mt-2.5">
            <input
              type="checkbox"
              className="w-4 h-4 rounded accent-sage-600"
              checked={draft.behaviour_changed}
              onChange={(e) => updateField("behaviour_changed", e.target.checked)}
            />
            Gedrag afwijkend van normaal
          </label>
        </div>
      </div>

      {error && (
        <p className="text-red-700 text-sm mt-4 flex items-center gap-1.5">
          <AlertCircle size={14} />
          {error}
        </p>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="inline-flex items-center gap-2 bg-sage-600 hover:bg-sage-700 disabled:opacity-60 text-white text-sm font-medium px-6 py-3 rounded-full mt-8 shadow-softer transition-colors"
      >
        {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
        {saving ? "Bezig met opslaan…" : "Opslaan"}
      </button>
    </main>
  );
}
