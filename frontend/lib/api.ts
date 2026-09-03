const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DemoClient {
  id: string;
  display_name: string;
  care_plan_summary: string;
}

export async function listDemoClients(): Promise<DemoClient[]> {
  const res = await fetch(`${API_URL}/demo-clients`);
  if (!res.ok) throw new Error("Kon cliëntenlijst niet laden.");
  return res.json();
}

export async function createZorgmoment(demoClientId: string, plannedCareSummary: string) {
  const res = await fetch(`${API_URL}/zorgmomenten`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ demo_client_id: demoClientId, planned_care_summary: plannedCareSummary }),
  });
  if (!res.ok) throw new Error("Kon zorgmoment niet aanmaken.");
  return res.json();
}

export async function uploadRecording(zorgmomentId: string, audioBlob: Blob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "note.webm");
  const res = await fetch(`${API_URL}/zorgmomenten/${zorgmomentId}/record`, {
    method: "POST",
    body: formData,
  });
  const body = await res.json();
  if (!res.ok) {
    // The backend returns the error body flat (JSONResponse, not
    // HTTPException's detail-wrapped shape) — read body.message directly.
    throw new Error(body.message || "Transcriptie mislukt. Probeer het opnieuw.");
  }
  return body;
}
