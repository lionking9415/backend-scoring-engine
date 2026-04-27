-- ============================================================================
-- BEST Galaxy — Cosmic Integration Phase Migration
-- Tables for Demographics Intake + AI Generated Reports
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ============================================================================

-- Table: demographic_intakes
-- Stores demographic intake survey responses per user/assessment
CREATE TABLE IF NOT EXISTS demographic_intakes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    assessment_id TEXT,
    demographics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_demographic_intakes_user_id
    ON demographic_intakes (user_id);

CREATE INDEX IF NOT EXISTS idx_demographic_intakes_assessment_id
    ON demographic_intakes (assessment_id);

ALTER TABLE demographic_intakes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous inserts on demographics"
    ON demographic_intakes
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous reads on demographics"
    ON demographic_intakes
    FOR SELECT
    TO anon
    USING (true);

-- ============================================================================
-- Table: generated_reports
-- Stores AI-generated lens reports and Cosmic Integration reports
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    assessment_id TEXT NOT NULL,
    report_type TEXT NOT NULL,       -- STUDENT_SUCCESS, PERSONAL_LIFESTYLE, etc. or FULL_GALAXY
    sections JSONB NOT NULL,         -- {section_key: narrative_text, ...}
    validation JSONB,                -- validation results from compliance checker
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generated_reports_user_id
    ON generated_reports (user_id);

CREATE INDEX IF NOT EXISTS idx_generated_reports_assessment_id
    ON generated_reports (assessment_id);

CREATE INDEX IF NOT EXISTS idx_generated_reports_report_type
    ON generated_reports (report_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_generated_reports_unique_lens
    ON generated_reports (user_id, assessment_id, report_type);

ALTER TABLE generated_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous inserts on generated_reports"
    ON generated_reports
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous reads on generated_reports"
    ON generated_reports
    FOR SELECT
    TO anon
    USING (true);

-- Allow updates (for re-generation)
CREATE POLICY "Allow anonymous updates on generated_reports"
    ON generated_reports
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);
