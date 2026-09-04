"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { extractZorgmoment, saveZorgmoment, ExtractionDraft } from "@/lib/api";

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

  if (loading) return <main className="max-w-xl mx-auto p-6">Bezig met concept maken…</main>;
  if (error && !draft) return <main className="max-w-xl mx-auto p-6 text-red-700">{error}</main>;
  if (!draft) return null;

  return (
    <main className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-2">Controleren en opslaan</h1>
      <p className="text-sm text-slate-600 mb-4">
        AI doet een voorstel. Jij controleert en beslist.
      </p>

      <label className="block text-sm font-medium mt-4">Ruwe transcriptie (audio-opname)</label>
      <div className="border rounded p-2 w-full bg-slate-50 text-slate-700 whitespace-pre-wrap">
        {transcript || "(geen transcriptie beschikbaar)"}
      </div>

      <label className="block text-sm font-medium mt-4">Uitgevoerde zorg</label>
      <textarea
        className="border rounded p-2 w-full"
        value={draft.actual_care_summary}
        onChange={(e) => updateField("actual_care_summary", e.target.value)}
      />

      <label className="flex items-center gap-2 mt-4">
        <input
          type="checkbox"
          checked={draft.deviation_detected}
          onChange={(e) => updateField("deviation_detected", e.target.checked)}
        />
        Afwijking van planning
      </label>
      {draft.deviation_detected && (
        <input
          className="border rounded p-2 w-full mt-2"
          value={draft.deviation_reason ?? ""}
          onChange={(e) => updateField("deviation_reason", e.target.value)}
          placeholder="Reden voor afwijking"
        />
      )}

      <label className="block text-sm font-medium mt-4">Stemming</label>
      <input
        className="border rounded p-2 w-full"
        value={draft.mood_observation}
        onChange={(e) => updateField("mood_observation", e.target.value)}
      />
      <label className="flex items-center gap-2 mt-2">
        <input
          type="checkbox"
          checked={draft.mood_changed}
          onChange={(e) => updateField("mood_changed", e.target.checked)}
        />
        Stemming afwijkend van normaal
      </label>

      <label className="block text-sm font-medium mt-4">Gedrag</label>
      <input
        className="border rounded p-2 w-full"
        value={draft.behaviour_observation}
        onChange={(e) => updateField("behaviour_observation", e.target.value)}
      />
      <label className="flex items-center gap-2 mt-2">
        <input
          type="checkbox"
          checked={draft.behaviour_changed}
          onChange={(e) => updateField("behaviour_changed", e.target.checked)}
        />
        Gedrag afwijkend van normaal
      </label>

      {error && <p className="text-red-700 mt-4">{error}</p>}

      <button
        onClick={handleSave}
        disabled={saving}
        className="bg-slate-900 text-white px-4 py-2 rounded mt-6"
      >
        {saving ? "Bezig met opslaan…" : "Opslaan"}
      </button>
    </main>
  );
}
