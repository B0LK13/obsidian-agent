-- Initialize Vibe.d Development Database
-- This script runs automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create application schema
CREATE SCHEMA IF NOT EXISTS app;

-- Example users table
CREATE TABLE IF NOT EXISTS app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Example sessions table
CREATE TABLE IF NOT EXISTS app.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app.users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON app.sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON app.sessions(user_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA app TO vibed;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO vibed;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO vibed;

-- Insert test data (development only)
INSERT INTO app.users (email, password_hash)
VALUES ('test@example.com', crypt('password123', gen_salt('bf')))
ON CONFLICT (email) DO NOTHING;

COMMENT ON TABLE app.users IS 'Application users';
COMMENT ON TABLE app.sessions IS 'User sessions for authentication';
