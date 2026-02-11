"""
SchoolCRM Data Migration: MongoDB Backups to Supabase
=====================================================
Uses Supabase REST API (no direct PostgreSQL connection needed)
"""

import os
import json
import uuid
from datetime import datetime

os.chdir('/app/backend')
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

from supabase import create_client

# Initialize Supabase client
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase = create_client(url, key)

BACKUP_DIR = '/app/backups/mongodb_backup'

# ID mappings (mongo_id -> uuid)
user_map = {}
client_map = {}
tariff_map = {}
group_map = {}
status_map = {}

def load_backup(collection_name):
    """Load JSON backup file"""
    path = f'{BACKUP_DIR}/{collection_name}.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def parse_datetime(dt_val):
    """Convert datetime to ISO string"""
    if not dt_val:
        return None
    if isinstance(dt_val, str):
        return dt_val.replace('Z', '+00:00')
    return dt_val

def migrate_users():
    """Migrate users collection"""
    print('\n=== Migrating Users ===')
    users = load_backup('users')
    
    for user in users:
        mongo_id = user.get('_id')
        new_uuid = str(uuid.uuid4())
        
        data = {
            'id': new_uuid,
            'mongo_id': mongo_id,
            'name': user.get('name'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'password': user.get('password'),
            'role': user.get('role', 'manager'),
            'telegram_id': user.get('telegram_id'),
            'telegram_username': user.get('telegram_username'),
            'telegram_first_name': user.get('telegram_first_name'),
            'telegram_linked_at': parse_datetime(user.get('telegram_linked_at')),
            'created_at': parse_datetime(user.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('users').insert(data).execute()
            user_map[mongo_id] = new_uuid
            print(f'  ✓ {user.get("name")} ({user.get("email")})')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {len(user_map)} users')

def migrate_statuses():
    """Migrate statuses collection"""
    print('\n=== Migrating Statuses ===')
    statuses = load_backup('statuses')
    
    for status in statuses:
        mongo_id = status.get('_id')
        new_uuid = str(uuid.uuid4())
        
        data = {
            'id': new_uuid,
            'mongo_id': mongo_id,
            'name': status.get('name'),
            'color': status.get('color', '#3B82F6'),
            'sort_order': status.get('order', 0),
            'is_default': status.get('is_default', False),
            'created_at': datetime.now().isoformat()
        }
        
        try:
            supabase.table('statuses').insert(data).execute()
            status_map[mongo_id] = new_uuid
            print(f'  ✓ {status.get("name")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {len(status_map)} statuses')

def migrate_groups():
    """Migrate groups collection"""
    print('\n=== Migrating Groups ===')
    groups = load_backup('groups')
    
    for group in groups:
        mongo_id = group.get('_id')
        new_uuid = str(uuid.uuid4())
        
        data = {
            'id': new_uuid,
            'mongo_id': mongo_id,
            'name': group.get('name'),
            'color': group.get('color', '#6B7280'),
            'description': group.get('description'),
            'created_at': parse_datetime(group.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('groups').insert(data).execute()
            group_map[mongo_id] = new_uuid
            print(f'  ✓ {group.get("name")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {len(group_map)} groups')

def migrate_tariffs():
    """Migrate tariffs collection"""
    print('\n=== Migrating Tariffs ===')
    tariffs = load_backup('tariffs')
    
    for tariff in tariffs:
        mongo_id = tariff.get('_id')
        new_uuid = str(uuid.uuid4())
        
        data = {
            'id': new_uuid,
            'mongo_id': mongo_id,
            'name': tariff.get('name'),
            'price': float(tariff.get('price', 0)),
            'currency': tariff.get('currency', 'USD'),
            'description': tariff.get('description'),
            'created_at': parse_datetime(tariff.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('tariffs').insert(data).execute()
            tariff_map[mongo_id] = new_uuid
            print(f'  ✓ {tariff.get("name")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {len(tariff_map)} tariffs')

def migrate_clients():
    """Migrate clients collection"""
    print('\n=== Migrating Clients ===')
    clients = load_backup('clients')
    
    for client in clients:
        mongo_id = client.get('_id')
        new_uuid = str(uuid.uuid4())
        
        # Map foreign keys
        manager_uuid = user_map.get(client.get('manager_id'))
        tariff_uuid = tariff_map.get(client.get('tariff_id'))
        group_uuid = group_map.get(client.get('group_id'))
        
        data = {
            'id': new_uuid,
            'mongo_id': mongo_id,
            'name': client.get('name'),
            'phone': client.get('phone', ''),
            'source': client.get('source'),
            'status': client.get('status', 'new'),
            'manager_id': manager_uuid,
            'tariff_id': tariff_uuid,
            'group_id': group_uuid,
            'is_lead': client.get('is_lead', False),
            'archived': client.get('archived', False),
            'created_at': parse_datetime(client.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('clients').insert(data).execute()
            client_map[mongo_id] = new_uuid
            print(f'  ✓ {client.get("name")} ({client.get("phone")})')
        except Exception as e:
            print(f'  ✗ Error for {client.get("name")}: {e}')
    
    print(f'Migrated {len(client_map)} clients')

def migrate_payments():
    """Migrate payments collection"""
    print('\n=== Migrating Payments ===')
    payments = load_backup('payments')
    count = 0
    
    for payment in payments:
        mongo_id = payment.get('_id')
        client_uuid = client_map.get(payment.get('client_id'))
        user_uuid = user_map.get(payment.get('user_id'))
        
        if not client_uuid:
            print(f'  ⚠ Skipping payment - client not found')
            continue
        
        data = {
            'id': str(uuid.uuid4()),
            'mongo_id': mongo_id,
            'client_id': client_uuid,
            'user_id': user_uuid,
            'amount': float(payment.get('amount', 0)),
            'currency': payment.get('currency', 'USD'),
            'status': payment.get('status', 'pending'),
            'payment_date': parse_datetime(payment.get('date')),
            'comment': payment.get('comment'),
            'created_at': parse_datetime(payment.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('payments').insert(data).execute()
            count += 1
            print(f'  ✓ Payment ${payment.get("amount")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {count} payments')

def migrate_reminders():
    """Migrate reminders collection"""
    print('\n=== Migrating Reminders ===')
    reminders = load_backup('reminders')
    count = 0
    
    for reminder in reminders:
        mongo_id = reminder.get('_id')
        client_uuid = client_map.get(reminder.get('client_id'))
        user_uuid = user_map.get(reminder.get('user_id'))
        
        if not client_uuid:
            print(f'  ⚠ Skipping reminder - client not found')
            continue
        
        data = {
            'id': str(uuid.uuid4()),
            'mongo_id': mongo_id,
            'client_id': client_uuid,
            'user_id': user_uuid,
            'text': reminder.get('text'),
            'remind_at': parse_datetime(reminder.get('remind_at')),
            'is_completed': reminder.get('is_completed', False),
            'notified': reminder.get('notified', False),
            'telegram_sent': reminder.get('telegram_sent', False),
            'telegram_sent_at': parse_datetime(reminder.get('telegram_sent_at')),
            'telegram_success': reminder.get('telegram_success'),
            'created_at': parse_datetime(reminder.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('reminders').insert(data).execute()
            count += 1
            print(f'  ✓ Reminder: {reminder.get("text")[:30]}...')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {count} reminders')

def migrate_notes():
    """Migrate notes collection"""
    print('\n=== Migrating Notes ===')
    notes = load_backup('notes')
    count = 0
    
    for note in notes:
        mongo_id = note.get('_id')
        client_uuid = client_map.get(note.get('client_id'))
        user_uuid = user_map.get(note.get('user_id'))
        
        if not client_uuid:
            print(f'  ⚠ Skipping note - client not found')
            continue
        
        data = {
            'id': str(uuid.uuid4()),
            'mongo_id': mongo_id,
            'client_id': client_uuid,
            'user_id': user_uuid,
            'text': note.get('text'),
            'created_at': parse_datetime(note.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('notes').insert(data).execute()
            count += 1
            print(f'  ✓ Note: {note.get("text")[:30]}...')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {count} notes')

def migrate_audio_files():
    """Migrate audio files collection"""
    print('\n=== Migrating Audio Files ===')
    files = load_backup('audio_files')
    count = 0
    
    for file in files:
        mongo_id = file.get('_id')
        client_uuid = client_map.get(file.get('client_id'))
        user_uuid = user_map.get(file.get('user_id'))
        
        if not client_uuid:
            print(f'  ⚠ Skipping audio - client not found')
            continue
        
        data = {
            'id': str(uuid.uuid4()),
            'mongo_id': mongo_id,
            'client_id': client_uuid,
            'user_id': user_uuid,
            'filename': file.get('filename'),
            'original_name': file.get('original_name'),
            'content_type': file.get('content_type'),
            'created_at': parse_datetime(file.get('created_at')) or datetime.now().isoformat()
        }
        
        try:
            supabase.table('audio_files').insert(data).execute()
            count += 1
            print(f'  ✓ Audio: {file.get("original_name")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {count} audio files')

def migrate_settings():
    """Migrate settings collection"""
    print('\n=== Migrating Settings ===')
    settings = load_backup('settings')
    count = 0
    
    for setting in settings:
        data = {
            'id': str(uuid.uuid4()),
            'key': setting.get('key', 'system'),
            'currency': setting.get('currency', 'USD'),
            'data': setting,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            supabase.table('settings').insert(data).execute()
            count += 1
            print(f'  ✓ Setting: {setting.get("key", "system")}')
        except Exception as e:
            print(f'  ✗ Error: {e}')
    
    print(f'Migrated {count} settings')

def migrate_activity_log():
    """Migrate activity log collection (batch)"""
    print('\n=== Migrating Activity Log ===')
    logs = load_backup('activity_log')
    count = 0
    
    # Process in batches
    batch_size = 20
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        batch_data = []
        
        for log in batch:
            data = {
                'id': str(uuid.uuid4()),
                'mongo_id': log.get('_id'),
                'user_id': log.get('user_id'),
                'user_name': log.get('user_name'),
                'action': log.get('action'),
                'entity_type': log.get('entity_type'),
                'entity_id': log.get('entity_id'),
                'details': log.get('details', {}),
                'created_at': parse_datetime(log.get('created_at')) or datetime.now().isoformat()
            }
            batch_data.append(data)
        
        try:
            supabase.table('activity_log').insert(batch_data).execute()
            count += len(batch_data)
            print(f'  ✓ Batch {i//batch_size + 1}: {len(batch_data)} logs')
        except Exception as e:
            print(f'  ✗ Batch error: {e}')
    
    print(f'Migrated {count} activity logs')

def verify_migration():
    """Verify all data was migrated"""
    print('\n' + '='*60)
    print('MIGRATION VERIFICATION')
    print('='*60)
    
    tables = ['users', 'clients', 'payments', 'reminders', 'notes', 
              'statuses', 'groups', 'tariffs', 'settings', 'activity_log', 'audio_files']
    
    for table in tables:
        try:
            response = supabase.table(table).select('count', count='exact').limit(0).execute()
            print(f'  {table}: {response.count} records')
        except Exception as e:
            print(f'  {table}: Error - {e}')

def main():
    print('='*60)
    print('SchoolCRM Data Migration to Supabase')
    print('='*60)
    
    # Migrate in order (respecting foreign keys)
    migrate_users()
    migrate_statuses()
    migrate_groups()
    migrate_tariffs()
    migrate_clients()
    migrate_payments()
    migrate_reminders()
    migrate_notes()
    migrate_audio_files()
    migrate_settings()
    migrate_activity_log()
    
    verify_migration()
    
    print('\n' + '='*60)
    print('✅ DATA MIGRATION COMPLETE')
    print('='*60)
    print('\nID Mappings saved:')
    print(f'  Users: {len(user_map)}')
    print(f'  Clients: {len(client_map)}')
    print(f'  Groups: {len(group_map)}')
    print(f'  Tariffs: {len(tariff_map)}')
    print(f'  Statuses: {len(status_map)}')

if __name__ == '__main__':
    main()
