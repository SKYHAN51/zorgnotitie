"use client";

import { useState, useRef, useEffect } from "react";
import { createZorgmoment, uploadRecording, listDemoClients, DemoClient } from "@/lib/api";
import { Mic, Square, Loader2, CheckCircle2, AlertCircle, ArrowRight, Users } from "lucide-react";

type Status = "idle" | "recording" | "uploading" | "transcribed" | "error";

export default function OpnemenPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<DemoClient | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [zorgmomentId, setZorgmomentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    listDemoClients()
      .then((data) => {
        setClients(data);
        setSelectedClient(data[0] ?? null);
      })
      .catch((err) => setErrorMessage(err instanceof Error ? err.message : "Onbekende fout."))
      .finally(() => setLoading(false));
  }, []);

  async function startRecording() {
    if (!selectedClient) return;
    setErrorMessage("");
    const zm = await createZorgmoment(selectedClient.id, selectedClient.care_plan_summary);
    setZorgmomentId(zm.id);

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.start();
    mediaRecorderRef.current = recorder;
    setStatus("recording");
  }

  async function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || !zorgmomentId) return;

    setStatus("uploading");
    recorder.stop();
    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      try {
        await uploadRecording(zorgmomentId, blob);
        setStatus("transcribed");
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "Onbekende fout.");
        setStatus("error");
      }
    };
  }

  if (loading) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-stone-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Cliënten laden…</p>
      </main>
    );
  }

  if (errorMessage && !selectedClient) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh]">
        <AlertCircle className="text-red-500" size={28} />
        <p className="text-red-700 text-sm">{errorMessage}</p>
      </main>
    );
  }

  if (!selectedClient && clients.length === 0) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh] text-stone-400">
        <Users size={28} />
        <p className="text-sm">Geen cliënten beschikbaar.</p>
      </main>
    );
  }

  if (!selectedClient) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-stone-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Cliënten laden…</p>
      </main>
    );
  }

  return (
    <main className="max-w-xl mx-auto px-6 pt-12 pb-16">
      <h1 className="text-3xl font-bold tracking-tight text-stone-900 mb-1.5">Opnemen</h1>
      <p className="text-stone-500 mb-8">Spreek een korte notitie in na een zorgmoment.</p>

      <div className="bg-white rounded-3xl shadow-soft p-6 mb-6">
        <label className="block mb-2 text-sm font-medium text-stone-600">Cliënt</label>
        <select
          className="border border-stone-200 rounded-xl px-3.5 py-2.5 w-full mb-4 text-base bg-cream-50 focus:outline-none focus:ring-2 focus:ring-sage-400 focus:border-sage-400"
          value={selectedClient.id}
          onChange={(e) => setSelectedClient(clients.find((c) => c.id === e.target.value) ?? null)}
          disabled={status === "recording" || status === "uploading"}
        >
          {clients.map((c) => (
            <option key={c.id} value={c.id}>{c.display_name}</option>
          ))}
        </select>

        <div className="bg-sage-50 rounded-2xl p-4 text-sm text-sage-900">
          <span className="block text-xs font-semibold text-sage-600 uppercase tracking-wide mb-1">
            Geplande zorg
          </span>
          {selectedClient.care_plan_summary}
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-soft p-8 flex flex-col items-center text-center">
        {status === "idle" && (
          <>
            <button
              onClick={startRecording}
              className="w-20 h-20 rounded-full bg-sage-600 hover:bg-sage-700 text-white flex items-center justify-center shadow-soft transition-all hover:scale-105 active:scale-95"
            >
              <Mic size={30} />
            </button>
            <p className="text-sm text-stone-400 mt-4">Tik om op te nemen</p>
          </>
        )}
        {status === "recording" && (
          <>
            <button
              onClick={stopRecording}
              className="w-20 h-20 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center shadow-soft animate-pulse transition-colors"
            >
              <Square size={24} fill="white" />
            </button>
            <p className="text-sm text-red-600 font-medium mt-4">Bezig met opnemen…</p>
          </>
        )}
        {status === "uploading" && (
          <>
            <div className="w-20 h-20 rounded-full bg-stone-100 flex items-center justify-center">
              <Loader2 className="animate-spin text-stone-400" size={28} />
            </div>
            <p className="text-sm text-stone-500 mt-4">Bezig met transcriberen…</p>
          </>
        )}
        {status === "transcribed" && (
          <>
            <CheckCircle2 className="text-sage-500" size={44} />
            <p className="text-sage-800 font-medium mt-3 mb-5">Transcriptie gelukt.</p>
            <a
              href={`/review/${zorgmomentId}`}
              className="inline-flex items-center gap-2 bg-sage-600 hover:bg-sage-700 text-white text-sm font-medium px-5 py-2.5 rounded-full transition-colors"
            >
              Ga naar controleren en opslaan
              <ArrowRight size={16} />
            </a>
          </>
        )}
        {status === "error" && (
          <>
            <AlertCircle className="text-red-500" size={32} />
            <p className="text-red-700 text-sm mt-2 mb-5">{errorMessage}</p>
            <button
              onClick={() => setStatus("idle")}
              className="bg-stone-800 hover:bg-stone-900 text-white text-sm font-medium px-5 py-2.5 rounded-full transition-colors"
            >
              Opnieuw proberen
            </button>
          </>
        )}
      </div>
    </main>
  );
}
