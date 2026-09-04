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

export interface ExtractionDraft {
  actual_care_summary: string;
  deviation_detected: boolean;
  deviation_reason: string | null;
  mood_observation: string;
  mood_changed: boolean;
  behaviour_observation: string;
  behaviour_changed: boolean;
}

export async function extractZorgmoment(
  zorgmomentId: string
): Promise<{ extraction_json: ExtractionDraft; transcript: string }> {
  const res = await fetch(`${API_URL}/zorgmomenten/${zorgmomentId}/extract`, { method: "POST" });
  const body = await res.json();
  // Flat JSONResponse body, same reasoning as uploadRecording above.
  if (!res.ok) throw new Error(body.message || "Extractie mislukt.");
  return body;
}

export async function saveZorgmoment(zorgmomentId: string, draft: ExtractionDraft, reviewedBy: string) {
  const res = await fetch(`${API_URL}/zorgmomenten/${zorgmomentId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...draft, reviewed_by: reviewedBy }),
  });
  if (!res.ok) {
    // Unlike every other endpoint in this file, /save's errors come from
    // FastAPI's HTTPException(detail="...") — a plain string, not the flat
    // JSONResponse({"message": ...}) shape the STT/extract endpoints use.
    // FastAPI's default exception handler wraps that into {"detail": "..."},
    // so THIS function must read body.detail, not body.message. Don't
    // "fix" this to match the other functions — that would silently swap
    // back to the generic fallback message for every 404/409 from /save.
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Opslaan mislukt.");
  }
  return res.json();
}

export async function listReviewedZorgmomenten() {
  const res = await fetch(`${API_URL}/dashboard/zorgmomenten`);
  if (!res.ok) throw new Error("Kon overzicht niet laden.");
  return res.json();
}

export async function getZorgmomentDetail(id: string) {
  const res = await fetch(`${API_URL}/dashboard/zorgmomenten/${id}`);
  if (!res.ok) throw new Error("Kon detail niet laden.");
  return res.json();
}

export async function listOpenAlerts() {
  const res = await fetch(`${API_URL}/dashboard/alerts?status=open`);
  if (!res.ok) throw new Error("Kon aandachtspunten niet laden.");
  return res.json();
}
