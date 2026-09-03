-- ============================================================
-- ZorgNotitie — Initial Schema
-- Standalone Supabase project. No connection to any other
-- project's tables. RLS locked to service_role only — the
-- FastAPI backend is the sole writer/reader; the frontend never
-- talks to Supabase directly.
-- ============================================================

CREATE TABLE demo_clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name TEXT NOT NULL,
  care_plan_summary TEXT NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE zorgmomenten (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  demo_client_id UUID REFERENCES demo_clients(id) ON DELETE CASCADE,
  planned_care_summary TEXT NOT NULL,
  audio_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (audio_status IN ('pending', 'transcribing', 'transcribed', 'failed')),
  transcript TEXT,
  extraction_json JSONB,
  actual_care_summary TEXT,
  deviation_detected BOOLEAN,
  deviation_reason TEXT,
  mood_observation TEXT,
  mood_changed BOOLEAN,
  behaviour_observation TEXT,
  behaviour_changed BOOLEAN,
  review_status TEXT NOT NULL DEFAULT 'processing'
    CHECK (review_status IN ('processing', 'draft', 'needs_review', 'reviewed', 'failed')),
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  zorgmoment_id UUID REFERENCES zorgmomenten(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL
    CHECK (alert_type IN ('care_deviation', 'mood_change', 'behaviour_change')),
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'acknowledged', 'resolved')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  acknowledged_at TIMESTAMPTZ,
  resolved_at TIMESTAMPTZ
);

CREATE TABLE processing_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  zorgmoment_id UUID REFERENCES zorgmomenten(id) ON DELETE CASCADE,
  stage TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('started', 'succeeded', 'failed')),
  error_code TEXT,
  error_message_safe TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  zorgmoment_id UUID REFERENCES zorgmomenten(id) ON DELETE CASCADE,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('ai', 'human')),
  event_type TEXT NOT NULL,
  before_json JSONB,
  after_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zorgmomenten_review_status ON zorgmomenten(review_status);
CREATE INDEX idx_zorgmomenten_client ON zorgmomenten(demo_client_id, created_at DESC);
CREATE INDEX idx_alerts_zorgmoment ON alerts(zorgmoment_id);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_processing_events_zorgmoment ON processing_events(zorgmoment_id, created_at);

-- ============================================================
-- RLS: service_role only. anon/authenticated get nothing — the
-- frontend has no direct Supabase credentials at all.
-- ============================================================
ALTER TABLE demo_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE zorgmomenten ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON demo_clients FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all" ON zorgmomenten FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all" ON alerts FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all" ON processing_events FOR ALL TO service_role USING (true);
CREATE POLICY "service_role_all" ON audit_log FOR ALL TO service_role USING (true);
