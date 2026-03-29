-- ============================================================================
-- BEST Executive Function Galaxy Assessment™ — Supabase Migration
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ============================================================================

-- Table: assessment_results
-- Stores all completed assessment results with full output JSON
CREATE TABLE IF NOT EXISTS assessment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    report_type TEXT NOT NULL,
    quadrant TEXT NOT NULL,
    load_state TEXT NOT NULL,
    pei_score DOUBLE PRECISION NOT NULL,
    bhp_score DOUBLE PRECISION NOT NULL,
    load_balance DOUBLE PRECISION NOT NULL,
    archetype_id TEXT,
    completion_rate DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    low_confidence BOOLEAN NOT NULL DEFAULT FALSE,
    demographics JSONB,
    raw_responses JSONB NOT NULL,
    full_output JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Phase 2: Payment tracking
    payment_status TEXT NOT NULL DEFAULT 'free',  -- 'free' or 'paid'
    payment_id TEXT,  -- Stripe payment intent ID
    upgraded_at TIMESTAMPTZ  -- When user upgraded to paid
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_assessment_results_user_id
    ON assessment_results (user_id);

CREATE INDEX IF NOT EXISTS idx_assessment_results_created_at
    ON assessment_results (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_assessment_results_report_type
    ON assessment_results (report_type);

CREATE INDEX IF NOT EXISTS idx_assessment_results_quadrant
    ON assessment_results (quadrant);

CREATE INDEX IF NOT EXISTS idx_assessment_results_payment_status
    ON assessment_results (payment_status);

-- Enable Row Level Security (RLS)
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous inserts (for API submissions)
CREATE POLICY "Allow anonymous inserts"
    ON assessment_results
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Allow anonymous reads (for result retrieval)
CREATE POLICY "Allow anonymous reads"
    ON assessment_results
    FOR SELECT
    TO anon
    USING (true);

-- ============================================================================
-- Optional: Table for AIMS function tracking (Phase 2)
-- ============================================================================

CREATE TABLE IF NOT EXISTS aims_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessment_results(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    subdomain TEXT NOT NULL,
    aims_function TEXT NOT NULL,  -- ATTENTION, SENSORY, ESCAPE, OVERWHELM
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aims_responses_assessment_id
    ON aims_responses (assessment_id);

ALTER TABLE aims_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous inserts on aims"
    ON aims_responses
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous reads on aims"
    ON aims_responses
    FOR SELECT
    TO anon
    USING (true);
