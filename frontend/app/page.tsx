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
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-slate-400 min-h-[60vh]">
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
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 min-h-[60vh] text-slate-400">
        <Users size={28} />
        <p className="text-sm">Geen cliënten beschikbaar.</p>
      </main>
    );
  }

  if (!selectedClient) {
    return (
      <main className="max-w-xl mx-auto p-6 flex flex-col items-center justify-center gap-3 text-slate-400 min-h-[60vh]">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm">Cliënten laden…</p>
      </main>
    );
  }

  return (
    <main className="max-w-xl mx-auto p-6 pt-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1">Opnemen</h1>
      <p className="text-sm text-slate-500 mb-6">Spreek een korte notitie in na een zorgmoment.</p>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 mb-5">
        <label className="block mb-2 text-sm font-medium text-slate-700">Cliënt</label>
        <select
          className="border border-slate-300 rounded-lg px-3 py-2 w-full mb-4 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          value={selectedClient.id}
          onChange={(e) => setSelectedClient(clients.find((c) => c.id === e.target.value) ?? null)}
          disabled={status === "recording" || status === "uploading"}
        >
          {clients.map((c) => (
            <option key={c.id} value={c.id}>{c.display_name}</option>
          ))}
        </select>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm text-slate-600">
          <span className="block text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">
            Geplande zorg
          </span>
          {selectedClient.care_plan_summary}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 flex flex-col items-center text-center">
        {status === "idle" && (
          <>
            <button
              onClick={startRecording}
              className="w-16 h-16 rounded-full bg-teal-600 hover:bg-teal-700 text-white flex items-center justify-center shadow-md transition-colors"
            >
              <Mic size={26} />
            </button>
            <p className="text-sm text-slate-400 mt-3">Start opname</p>
          </>
        )}
        {status === "recording" && (
          <>
            <button
              onClick={stopRecording}
              className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center shadow-md animate-pulse transition-colors"
            >
              <Square size={22} fill="white" />
            </button>
            <p className="text-sm text-red-600 font-medium mt-3">Bezig met opnemen…</p>
          </>
        )}
        {status === "uploading" && (
          <>
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
              <Loader2 className="animate-spin text-slate-400" size={26} />
            </div>
            <p className="text-sm text-slate-500 mt-3">Bezig met transcriberen…</p>
          </>
        )}
        {status === "transcribed" && (
          <>
            <CheckCircle2 className="text-emerald-500" size={40} />
            <p className="text-emerald-700 font-medium mt-2 mb-4">Transcriptie gelukt.</p>
            <a
              href={`/review/${zorgmomentId}`}
              className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Ga naar controleren en opslaan
              <ArrowRight size={16} />
            </a>
          </>
        )}
        {status === "error" && (
          <>
            <AlertCircle className="text-red-500" size={32} />
            <p className="text-red-700 text-sm mt-2 mb-4">{errorMessage}</p>
            <button
              onClick={() => setStatus("idle")}
              className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Opnieuw proberen
            </button>
          </>
        )}
      </div>
    </main>
  );
}
