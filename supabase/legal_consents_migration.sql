-- Audit log of user consent to legal terms before assessment.
-- Captures *which exact legal version* the user agreed to, plus the
-- individual checkbox state and a UTC timestamp — evidence that the
-- gate was passed if liability is ever questioned.
--
-- Apply with:
--   supabase db reset                        (local)
-- or
--   psql "$DATABASE_URL" -f supabase/legal_consents_migration.sql

CREATE TABLE IF NOT EXISTS legal_consents (
    id              uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         text          NULL,
    legal_version   text          NOT NULL,
    consents        jsonb         NOT NULL DEFAULT '{}'::jsonb,
    user_agent      text          NULL,
    recorded_at     timestamptz   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_legal_consents_user_id
    ON legal_consents (user_id);

CREATE INDEX IF NOT EXISTS idx_legal_consents_recorded_at
    ON legal_consents (recorded_at DESC);

COMMENT ON TABLE  legal_consents IS
    'Append-only consent log for the BEST Galaxy pre-assessment legal gate.';
COMMENT ON COLUMN legal_consents.legal_version IS
    'Version of the legal copy the user accepted (matches LEGAL_VERSION constant).';
COMMENT ON COLUMN legal_consents.consents IS
    'Per-checkbox state, e.g. {"terms": true, "responsibility": true, "research": false}.';
