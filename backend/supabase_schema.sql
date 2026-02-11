-- ============================================================
-- SchoolCRM Database Schema for Supabase
-- ============================================================
-- Run this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/jgdhcsznuhrsaxlqfesb/sql
-- ============================================================

-- Enable UUID extension (usually already enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'manager',
    telegram_id VARCHAR(50),
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    telegram_linked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 2. STATUSES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS statuses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(20) DEFAULT '#3B82F6',
    sort_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3. GROUPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(20) DEFAULT '#6B7280',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. TARIFFS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'USD',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. CLIENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    source VARCHAR(255),
    status VARCHAR(100) DEFAULT 'new',
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    tariff_id UUID REFERENCES tariffs(id) ON DELETE SET NULL,
    group_id UUID REFERENCES groups(id) ON DELETE SET NULL,
    is_lead BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 6. PAYMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending',
    payment_date TIMESTAMPTZ DEFAULT NOW(),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 7. REMINDERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    remind_at TIMESTAMPTZ NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    notified BOOLEAN DEFAULT FALSE,
    telegram_sent BOOLEAN DEFAULT FALSE,
    telegram_sent_at TIMESTAMPTZ,
    telegram_success BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 8. NOTES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 9. AUDIO FILES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS audio_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    content_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 10. SETTINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 11. ACTIVITY LOG TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    user_id VARCHAR(50),
    user_name VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(50),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 12. NOTIFICATIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(100),
    title VARCHAR(255),
    message TEXT,
    entity_type VARCHAR(100),
    entity_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_clients_manager ON clients(manager_id);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_clients_archived ON clients(archived);
CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_id);
CREATE INDEX IF NOT EXISTS idx_reminders_client ON reminders(client_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_client ON notes(client_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- ============================================================
-- ROW LEVEL SECURITY (Optional - Enable if needed)
-- ============================================================
-- For now, we'll use API key authentication
-- RLS can be enabled later for more granular access control

-- ============================================================
-- DONE! Tables created successfully.
-- ============================================================
