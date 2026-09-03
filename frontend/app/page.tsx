"use client";

import { useState, useRef, useEffect } from "react";
import { createZorgmoment, uploadRecording, listDemoClients, DemoClient } from "@/lib/api";

type Status = "idle" | "recording" | "uploading" | "transcribed" | "error";

export default function OpnemenPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<DemoClient | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [zorgmomentId, setZorgmomentId] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    listDemoClients()
      .then((data) => {
        setClients(data);
        setSelectedClient(data[0] ?? null);
      })
      .catch((err) => setErrorMessage(err instanceof Error ? err.message : "Onbekende fout."));
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

  if (!selectedClient) {
    return <main className="max-w-xl mx-auto p-6">{errorMessage || "Cliënten laden…"}</main>;
  }

  return (
    <main className="max-w-xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Opnemen</h1>

      <label className="block mb-2 text-sm font-medium">Cliënt</label>
      <select
        className="border rounded p-2 w-full mb-4"
        value={selectedClient.id}
        onChange={(e) => setSelectedClient(clients.find((c) => c.id === e.target.value) ?? null)}
        disabled={status === "recording" || status === "uploading"}
      >
        {clients.map((c) => (
          <option key={c.id} value={c.id}>{c.display_name}</option>
        ))}
      </select>

      <div className="bg-white border rounded p-3 mb-4 text-sm text-slate-600">
        <strong>Geplande zorg:</strong> {selectedClient.care_plan_summary}
      </div>

      {status === "idle" && (
        <button onClick={startRecording} className="bg-slate-900 text-white px-4 py-2 rounded">
          Start opname
        </button>
      )}
      {status === "recording" && (
        <button onClick={stopRecording} className="bg-red-600 text-white px-4 py-2 rounded">
          Stop opname
        </button>
      )}
      {status === "uploading" && <p>Bezig met transcriberen…</p>}
      {status === "transcribed" && (
        <div>
          <p className="text-green-700 mb-2">Transcriptie gelukt.</p>
          <a href={`/review/${zorgmomentId}`} className="underline text-slate-900">
            Ga naar controleren en opslaan →
          </a>
        </div>
      )}
      {status === "error" && (
        <div>
          <p className="text-red-700 mb-2">{errorMessage}</p>
          <button onClick={() => setStatus("idle")} className="bg-slate-900 text-white px-4 py-2 rounded">
            Opnieuw proberen
          </button>
        </div>
      )}
    </main>
  );
}
