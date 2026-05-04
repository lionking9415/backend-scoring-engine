-- Add email_confirmed and email_confirmed_at columns to users table
-- For email verification flow (Resend integration)

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmed_at TIMESTAMPTZ;

-- Index for quick lookups on unconfirmed users
CREATE INDEX IF NOT EXISTS idx_users_email_confirmed ON users (email_confirmed);
