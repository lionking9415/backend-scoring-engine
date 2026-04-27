-- ============================================================================
-- Per-Product Payment Model Migration
-- ============================================================================
--
-- Adds a `paid_products` JSONB array to the assessment_results table so each
-- assessment can independently unlock multiple SKUs (4 lens reports +
-- cosmic bundle + financial / health deep-dives + compatibility).
--
-- The legacy `payment_status` column is kept for backwards compatibility:
-- a row with `payment_status = 'paid'` is treated as "all SKUs unlocked".
-- New webhook events write to `paid_products` instead.
--
-- Safe to run multiple times.
-- ============================================================================

-- 1. Add the paid_products column (default empty array)
ALTER TABLE assessment_results
    ADD COLUMN IF NOT EXISTS paid_products JSONB NOT NULL DEFAULT '[]'::jsonb;

-- 2. Backfill: any row that was already marked 'paid' under the legacy
--    single-string flag should be treated as if every SKU was unlocked.
UPDATE assessment_results
SET paid_products = (
    '["PERSONAL_LIFESTYLE","STUDENT_SUCCESS","PROFESSIONAL_LEADERSHIP",'
    || '"FAMILY_ECOSYSTEM","COSMIC_BUNDLE","FINANCIAL_DEEP_DIVE",'
    || '"HEALTH_DEEP_DIVE","COMPATIBILITY"]'
)::jsonb
WHERE payment_status = 'paid'
  AND (paid_products IS NULL OR paid_products = '[]'::jsonb);

-- 3. Helpful index for "which assessments has user X paid for product Y"
CREATE INDEX IF NOT EXISTS idx_assessment_results_paid_products
    ON assessment_results USING GIN (paid_products);

-- 4. Sanity check
DO $$
BEGIN
    RAISE NOTICE 'paid_products migration complete.';
END $$;
