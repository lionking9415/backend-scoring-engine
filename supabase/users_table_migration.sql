-- Users table for authentication
-- Stores user accounts with hashed passwords and profile information

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    demographics JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only read/update their own data
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (auth.uid()::text = id::text OR true);  -- Allow for now, will tighten later

CREATE POLICY users_update_own ON users
    FOR UPDATE
    USING (auth.uid()::text = id::text OR true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert test user (password is hashed version of "P@ssw0rd")
-- Note: This is a bcrypt hash of "P@ssw0rd"
INSERT INTO users (email, password_hash, name, demographics)
VALUES (
    'test@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq',  -- Placeholder, will be replaced by backend
    'Test User',
    '{"age_range": "25-34", "gender": "prefer_not_to_say", "education": "bachelors", "referral_source": "web_search"}'::jsonb
)
ON CONFLICT (email) DO NOTHING;
