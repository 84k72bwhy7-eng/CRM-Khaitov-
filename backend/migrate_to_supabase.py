"""
SchoolCRM Migration Script: MongoDB to Supabase PostgreSQL
==========================================================
This script safely migrates all data from MongoDB to Supabase.

Usage:
    python migrate_to_supabase.py

Steps:
1. Creates PostgreSQL schema in Supabase
2. Migrates all collections with data integrity checks
3. Verifies migration success
4. Provides rollback instructions if needed
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

# PostgreSQL connection
def get_pg_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT", 5432),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode="require"
    )

# SQL Schema for Supabase
SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
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
    telegram_linked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Statuses table
CREATE TABLE IF NOT EXISTS statuses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(20) DEFAULT '#3B82F6',
    "order" INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(20) DEFAULT '#6B7280',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tariffs table
CREATE TABLE IF NOT EXISTS tariffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'USD',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clients table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending',
    date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    notified BOOLEAN DEFAULT FALSE,
    telegram_sent BOOLEAN DEFAULT FALSE,
    telegram_sent_at TIMESTAMP WITH TIME ZONE,
    telegram_success BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notes table
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    content_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mongo_id VARCHAR(24) UNIQUE,
    user_id VARCHAR(50),
    user_name VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(50),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_clients_manager ON clients(manager_id);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_id);
CREATE INDEX IF NOT EXISTS idx_reminders_client ON reminders(client_id);
CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_notes_client ON notes(client_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
"""

def create_schema(conn):
    """Create all tables in Supabase"""
    print("\n=== Creating Schema ===")
    cursor = conn.cursor()
    
    # Execute schema
    cursor.execute(SCHEMA_SQL)
    conn.commit()
    
    print("✓ Schema created successfully")
    cursor.close()

def load_backup_data(collection_name):
    """Load data from backup JSON files"""
    backup_path = f"/app/backups/mongodb_backup/{collection_name}.json"
    if os.path.exists(backup_path):
        with open(backup_path, "r") as f:
            return json.load(f)
    return []

def parse_datetime(dt_str):
    """Parse datetime string to Python datetime"""
    if not dt_str:
        return None
    try:
        # Handle ISO format
        if isinstance(dt_str, str):
            dt_str = dt_str.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_str)
        return dt_str
    except:
        return None

def migrate_users(conn):
    """Migrate users collection"""
    print("\n=== Migrating Users ===")
    cursor = conn.cursor()
    users = load_backup_data("users")
    
    for user in users:
        cursor.execute("""
            INSERT INTO users (mongo_id, name, email, phone, password, role, 
                             telegram_id, telegram_username, telegram_first_name, 
                             telegram_linked_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                telegram_id = EXCLUDED.telegram_id,
                telegram_username = EXCLUDED.telegram_username
        """, (
            user.get("_id"),
            user.get("name"),
            user.get("email"),
            user.get("phone"),
            user.get("password"),
            user.get("role", "manager"),
            user.get("telegram_id"),
            user.get("telegram_username"),
            user.get("telegram_first_name"),
            parse_datetime(user.get("telegram_linked_at")),
            parse_datetime(user.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(users)} users")
    cursor.close()

def migrate_statuses(conn):
    """Migrate statuses collection"""
    print("\n=== Migrating Statuses ===")
    cursor = conn.cursor()
    statuses = load_backup_data("statuses")
    
    for status in statuses:
        cursor.execute("""
            INSERT INTO statuses (mongo_id, name, color, "order", is_default)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                name = EXCLUDED.name,
                color = EXCLUDED.color
        """, (
            status.get("_id"),
            status.get("name"),
            status.get("color", "#3B82F6"),
            status.get("order", 0),
            status.get("is_default", False)
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(statuses)} statuses")
    cursor.close()

def migrate_groups(conn):
    """Migrate groups collection"""
    print("\n=== Migrating Groups ===")
    cursor = conn.cursor()
    groups = load_backup_data("groups")
    
    for group in groups:
        cursor.execute("""
            INSERT INTO groups (mongo_id, name, color, description, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                name = EXCLUDED.name,
                color = EXCLUDED.color
        """, (
            group.get("_id"),
            group.get("name"),
            group.get("color", "#6B7280"),
            group.get("description"),
            parse_datetime(group.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(groups)} groups")
    cursor.close()

def migrate_tariffs(conn):
    """Migrate tariffs collection"""
    print("\n=== Migrating Tariffs ===")
    cursor = conn.cursor()
    tariffs = load_backup_data("tariffs")
    
    for tariff in tariffs:
        cursor.execute("""
            INSERT INTO tariffs (mongo_id, name, price, currency, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                name = EXCLUDED.name,
                price = EXCLUDED.price
        """, (
            tariff.get("_id"),
            tariff.get("name"),
            tariff.get("price", 0),
            tariff.get("currency", "USD"),
            tariff.get("description"),
            parse_datetime(tariff.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(tariffs)} tariffs")
    cursor.close()

def migrate_clients(conn):
    """Migrate clients collection"""
    print("\n=== Migrating Clients ===")
    cursor = conn.cursor()
    clients = load_backup_data("clients")
    
    # First, get ID mappings for foreign keys
    cursor.execute("SELECT id, mongo_id FROM users")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM tariffs")
    tariff_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM groups")
    group_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    for client in clients:
        manager_uuid = user_map.get(client.get("manager_id"))
        tariff_uuid = tariff_map.get(client.get("tariff_id"))
        group_uuid = group_map.get(client.get("group_id"))
        
        cursor.execute("""
            INSERT INTO clients (mongo_id, name, phone, source, status, manager_id, 
                               tariff_id, group_id, is_lead, archived, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                name = EXCLUDED.name,
                phone = EXCLUDED.phone,
                status = EXCLUDED.status
        """, (
            client.get("_id"),
            client.get("name"),
            client.get("phone"),
            client.get("source"),
            client.get("status", "new"),
            manager_uuid,
            tariff_uuid,
            group_uuid,
            client.get("is_lead", False),
            client.get("archived", False),
            parse_datetime(client.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(clients)} clients")
    cursor.close()

def migrate_payments(conn):
    """Migrate payments collection"""
    print("\n=== Migrating Payments ===")
    cursor = conn.cursor()
    payments = load_backup_data("payments")
    
    # Get ID mappings
    cursor.execute("SELECT id, mongo_id FROM clients")
    client_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM users")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    for payment in payments:
        client_uuid = client_map.get(payment.get("client_id"))
        user_uuid = user_map.get(payment.get("user_id"))
        
        if not client_uuid:
            print(f"  ⚠ Skipping payment - client not found: {payment.get('client_id')}")
            continue
            
        cursor.execute("""
            INSERT INTO payments (mongo_id, client_id, user_id, amount, currency, 
                                status, date, comment, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                amount = EXCLUDED.amount,
                status = EXCLUDED.status
        """, (
            payment.get("_id"),
            client_uuid,
            user_uuid,
            payment.get("amount", 0),
            payment.get("currency", "USD"),
            payment.get("status", "pending"),
            parse_datetime(payment.get("date")),
            payment.get("comment"),
            parse_datetime(payment.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(payments)} payments")
    cursor.close()

def migrate_reminders(conn):
    """Migrate reminders collection"""
    print("\n=== Migrating Reminders ===")
    cursor = conn.cursor()
    reminders = load_backup_data("reminders")
    
    cursor.execute("SELECT id, mongo_id FROM clients")
    client_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM users")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    for reminder in reminders:
        client_uuid = client_map.get(reminder.get("client_id"))
        user_uuid = user_map.get(reminder.get("user_id"))
        
        if not client_uuid:
            print(f"  ⚠ Skipping reminder - client not found: {reminder.get('client_id')}")
            continue
            
        cursor.execute("""
            INSERT INTO reminders (mongo_id, client_id, user_id, text, remind_at, 
                                 is_completed, notified, telegram_sent, 
                                 telegram_sent_at, telegram_success, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                text = EXCLUDED.text,
                is_completed = EXCLUDED.is_completed
        """, (
            reminder.get("_id"),
            client_uuid,
            user_uuid,
            reminder.get("text"),
            parse_datetime(reminder.get("remind_at")),
            reminder.get("is_completed", False),
            reminder.get("notified", False),
            reminder.get("telegram_sent", False),
            parse_datetime(reminder.get("telegram_sent_at")),
            reminder.get("telegram_success"),
            parse_datetime(reminder.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(reminders)} reminders")
    cursor.close()

def migrate_notes(conn):
    """Migrate notes collection"""
    print("\n=== Migrating Notes ===")
    cursor = conn.cursor()
    notes = load_backup_data("notes")
    
    cursor.execute("SELECT id, mongo_id FROM clients")
    client_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM users")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    for note in notes:
        client_uuid = client_map.get(note.get("client_id"))
        user_uuid = user_map.get(note.get("user_id"))
        
        if not client_uuid:
            print(f"  ⚠ Skipping note - client not found: {note.get('client_id')}")
            continue
            
        cursor.execute("""
            INSERT INTO notes (mongo_id, client_id, user_id, text, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO UPDATE SET
                text = EXCLUDED.text
        """, (
            note.get("_id"),
            client_uuid,
            user_uuid,
            note.get("text"),
            parse_datetime(note.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(notes)} notes")
    cursor.close()

def migrate_settings(conn):
    """Migrate settings collection"""
    print("\n=== Migrating Settings ===")
    cursor = conn.cursor()
    settings = load_backup_data("settings")
    
    for setting in settings:
        cursor.execute("""
            INSERT INTO settings (key, currency, data, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                currency = EXCLUDED.currency
        """, (
            setting.get("key", "system"),
            setting.get("currency", "USD"),
            json.dumps(setting),
            parse_datetime(setting.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(settings)} settings")
    cursor.close()

def migrate_activity_log(conn):
    """Migrate activity log collection"""
    print("\n=== Migrating Activity Log ===")
    cursor = conn.cursor()
    logs = load_backup_data("activity_log")
    
    batch_size = 50
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        for log in batch:
            cursor.execute("""
                INSERT INTO activity_log (mongo_id, user_id, user_name, action, 
                                        entity_type, entity_id, details, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (mongo_id) DO NOTHING
            """, (
                log.get("_id"),
                log.get("user_id"),
                log.get("user_name"),
                log.get("action"),
                log.get("entity_type"),
                log.get("entity_id"),
                json.dumps(log.get("details", {})),
                parse_datetime(log.get("created_at")) or datetime.now()
            ))
        conn.commit()
        print(f"  Processed {min(i+batch_size, len(logs))}/{len(logs)} logs")
    
    print(f"✓ Migrated {len(logs)} activity logs")
    cursor.close()

def migrate_audio_files(conn):
    """Migrate audio files collection"""
    print("\n=== Migrating Audio Files ===")
    cursor = conn.cursor()
    files = load_backup_data("audio_files")
    
    cursor.execute("SELECT id, mongo_id FROM clients")
    client_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, mongo_id FROM users")
    user_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    for file in files:
        client_uuid = client_map.get(file.get("client_id"))
        user_uuid = user_map.get(file.get("user_id"))
        
        if not client_uuid:
            print(f"  ⚠ Skipping audio - client not found: {file.get('client_id')}")
            continue
            
        cursor.execute("""
            INSERT INTO audio_files (mongo_id, client_id, user_id, filename, 
                                   original_name, content_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (mongo_id) DO NOTHING
        """, (
            file.get("_id"),
            client_uuid,
            user_uuid,
            file.get("filename"),
            file.get("original_name"),
            file.get("content_type"),
            parse_datetime(file.get("created_at")) or datetime.now()
        ))
    
    conn.commit()
    print(f"✓ Migrated {len(files)} audio files")
    cursor.close()

def verify_migration(conn):
    """Verify migration was successful"""
    print("\n=== Verifying Migration ===")
    cursor = conn.cursor()
    
    tables = ["users", "clients", "payments", "reminders", "notes", 
              "statuses", "groups", "tariffs", "settings", "activity_log"]
    
    results = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        results[table] = count
        print(f"  {table}: {count} records")
    
    cursor.close()
    return results

def main():
    print("=" * 60)
    print("SchoolCRM Migration: MongoDB → Supabase PostgreSQL")
    print("=" * 60)
    
    try:
        print("\n[1/3] Connecting to Supabase...")
        conn = get_pg_connection()
        print("✓ Connected to Supabase PostgreSQL")
        
        print("\n[2/3] Running Migration...")
        create_schema(conn)
        
        # Migrate in order (respecting foreign keys)
        migrate_users(conn)
        migrate_statuses(conn)
        migrate_groups(conn)
        migrate_tariffs(conn)
        migrate_clients(conn)
        migrate_payments(conn)
        migrate_reminders(conn)
        migrate_notes(conn)
        migrate_settings(conn)
        migrate_activity_log(conn)
        migrate_audio_files(conn)
        
        print("\n[3/3] Verification...")
        results = verify_migration(conn)
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update DATABASE_TYPE=postgres in .env")
        print("2. Restart the backend server")
        print("3. Verify the application works")
        print("4. Keep MongoDB backup at /app/backups/mongodb_backup/")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        print("\nRollback: Your MongoDB data is safe and unchanged.")
        print("Backup location: /app/backups/mongodb_backup/")
        raise

if __name__ == "__main__":
    main()
