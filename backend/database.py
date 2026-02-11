"""
Supabase Database Client for SchoolCRM
=======================================
Handles all database operations via Supabase REST API
"""

import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

# Load environment
def load_env():
    """Load environment variables from .env file"""
    env_path = '/app/backend/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Initialize Supabase client
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabaseDB:
    """Database operations wrapper for Supabase"""
    
    # ==================== USERS ====================
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        result = supabase.table('users').select('*').eq('email', email).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: str) -> Optional[Dict]:
        """Get user by Telegram ID"""
        result = supabase.table('users').select('*').eq('telegram_id', str(telegram_id)).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_all_users() -> List[Dict]:
        """Get all users"""
        result = supabase.table('users').select('*').order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def create_user(user_data: Dict) -> Dict:
        """Create a new user"""
        result = supabase.table('users').insert(user_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_user(user_id: str, update_data: Dict) -> Dict:
        """Update a user"""
        result = supabase.table('users').update(update_data).eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete a user"""
        supabase.table('users').delete().eq('id', user_id).execute()
        return True
    
    # ==================== CLIENTS ====================
    
    @staticmethod
    def get_all_clients(filters: Dict = None, include_archived: bool = False) -> List[Dict]:
        """Get all clients with optional filters"""
        query = supabase.table('clients').select('*')
        
        if not include_archived:
            query = query.eq('archived', False)
        
        if filters:
            if filters.get('manager_id'):
                query = query.eq('manager_id', filters['manager_id'])
            if filters.get('status'):
                query = query.eq('status', filters['status'])
            if filters.get('is_lead') is not None:
                query = query.eq('is_lead', filters['is_lead'])
            if filters.get('group_id'):
                query = query.eq('group_id', filters['group_id'])
            if filters.get('search'):
                search = filters['search']
                query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%")
        
        result = query.order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_client_by_id(client_id: str) -> Optional[Dict]:
        """Get client by ID"""
        result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_client(client_data: Dict) -> Dict:
        """Create a new client"""
        result = supabase.table('clients').insert(client_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_client(client_id: str, update_data: Dict) -> Dict:
        """Update a client"""
        result = supabase.table('clients').update(update_data).eq('id', client_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_client(client_id: str) -> bool:
        """Delete a client"""
        supabase.table('clients').delete().eq('id', client_id).execute()
        return True
    
    @staticmethod
    def count_clients(filters: Dict = None) -> int:
        """Count clients"""
        query = supabase.table('clients').select('count', count='exact')
        if filters:
            if filters.get('manager_id'):
                query = query.eq('manager_id', filters['manager_id'])
            if filters.get('archived') is not None:
                query = query.eq('archived', filters['archived'])
        result = query.execute()
        return result.count or 0
    
    # ==================== NOTES ====================
    
    @staticmethod
    def get_notes_by_client(client_id: str) -> List[Dict]:
        """Get all notes for a client"""
        result = supabase.table('notes').select('*').eq('client_id', client_id).order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_recent_notes(limit: int = 10) -> List[Dict]:
        """Get recent notes"""
        result = supabase.table('notes').select('*').order('created_at', desc=True).limit(limit).execute()
        return result.data
    
    @staticmethod
    def create_note(note_data: Dict) -> Dict:
        """Create a new note"""
        result = supabase.table('notes').insert(note_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_note(note_id: str) -> bool:
        """Delete a note"""
        supabase.table('notes').delete().eq('id', note_id).execute()
        return True
    
    # ==================== PAYMENTS ====================
    
    @staticmethod
    def get_all_payments() -> List[Dict]:
        """Get all payments"""
        result = supabase.table('payments').select('*').order('payment_date', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_payments_by_client(client_id: str) -> List[Dict]:
        """Get payments for a client"""
        result = supabase.table('payments').select('*').eq('client_id', client_id).order('payment_date', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_payment_by_id(payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        result = supabase.table('payments').select('*').eq('id', payment_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_payment(payment_data: Dict) -> Dict:
        """Create a new payment"""
        result = supabase.table('payments').insert(payment_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_payment(payment_id: str, update_data: Dict) -> Dict:
        """Update a payment"""
        result = supabase.table('payments').update(update_data).eq('id', payment_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_payment(payment_id: str) -> bool:
        """Delete a payment"""
        supabase.table('payments').delete().eq('id', payment_id).execute()
        return True
    
    @staticmethod
    def sum_payments(filters: Dict = None) -> float:
        """Sum all payments (optionally filtered)"""
        query = supabase.table('payments').select('amount')
        if filters:
            if filters.get('status'):
                query = query.eq('status', filters['status'])
        result = query.execute()
        return sum(p.get('amount', 0) for p in result.data) if result.data else 0
    
    # ==================== REMINDERS ====================
    
    @staticmethod
    def get_all_reminders(user_id: str = None) -> List[Dict]:
        """Get all reminders"""
        query = supabase.table('reminders').select('*')
        if user_id:
            query = query.eq('user_id', user_id)
        result = query.order('remind_at', desc=False).execute()
        return result.data
    
    @staticmethod
    def get_overdue_reminders(user_id: str = None) -> List[Dict]:
        """Get overdue reminders"""
        now = datetime.now(timezone.utc).isoformat()
        query = supabase.table('reminders').select('*').lt('remind_at', now).eq('is_completed', False)
        if user_id:
            query = query.eq('user_id', user_id)
        result = query.order('remind_at', desc=False).execute()
        return result.data
    
    @staticmethod
    def get_due_reminders_for_telegram() -> List[Dict]:
        """Get reminders due for Telegram notification"""
        now = datetime.now(timezone.utc).isoformat()
        result = supabase.table('reminders').select('*').lt('remind_at', now).eq('is_completed', False).eq('telegram_sent', False).execute()
        return result.data
    
    @staticmethod
    def get_reminder_by_id(reminder_id: str) -> Optional[Dict]:
        """Get reminder by ID"""
        result = supabase.table('reminders').select('*').eq('id', reminder_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_reminder(reminder_data: Dict) -> Dict:
        """Create a new reminder"""
        result = supabase.table('reminders').insert(reminder_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_reminder(reminder_id: str, update_data: Dict) -> Dict:
        """Update a reminder"""
        result = supabase.table('reminders').update(update_data).eq('id', reminder_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_reminder(reminder_id: str) -> bool:
        """Delete a reminder"""
        supabase.table('reminders').delete().eq('id', reminder_id).execute()
        return True
    
    # ==================== STATUSES ====================
    
    @staticmethod
    def get_all_statuses() -> List[Dict]:
        """Get all statuses"""
        result = supabase.table('statuses').select('*').order('sort_order').execute()
        return result.data
    
    @staticmethod
    def get_status_by_id(status_id: str) -> Optional[Dict]:
        """Get status by ID"""
        result = supabase.table('statuses').select('*').eq('id', status_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def get_status_by_name(name: str) -> Optional[Dict]:
        """Get status by name"""
        result = supabase.table('statuses').select('*').eq('name', name).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_status(status_data: Dict) -> Dict:
        """Create a new status"""
        result = supabase.table('statuses').insert(status_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_status(status_id: str, update_data: Dict) -> Dict:
        """Update a status"""
        result = supabase.table('statuses').update(update_data).eq('id', status_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_status(status_id: str) -> bool:
        """Delete a status"""
        supabase.table('statuses').delete().eq('id', status_id).execute()
        return True
    
    # ==================== GROUPS ====================
    
    @staticmethod
    def get_all_groups() -> List[Dict]:
        """Get all groups"""
        result = supabase.table('groups').select('*').order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_group_by_id(group_id: str) -> Optional[Dict]:
        """Get group by ID"""
        result = supabase.table('groups').select('*').eq('id', group_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_group(group_data: Dict) -> Dict:
        """Create a new group"""
        result = supabase.table('groups').insert(group_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_group(group_id: str, update_data: Dict) -> Dict:
        """Update a group"""
        result = supabase.table('groups').update(update_data).eq('id', group_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_group(group_id: str) -> bool:
        """Delete a group"""
        supabase.table('groups').delete().eq('id', group_id).execute()
        return True
    
    # ==================== TARIFFS ====================
    
    @staticmethod
    def get_all_tariffs() -> List[Dict]:
        """Get all tariffs"""
        result = supabase.table('tariffs').select('*').order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_tariff_by_id(tariff_id: str) -> Optional[Dict]:
        """Get tariff by ID"""
        result = supabase.table('tariffs').select('*').eq('id', tariff_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_tariff(tariff_data: Dict) -> Dict:
        """Create a new tariff"""
        result = supabase.table('tariffs').insert(tariff_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def update_tariff(tariff_id: str, update_data: Dict) -> Dict:
        """Update a tariff"""
        result = supabase.table('tariffs').update(update_data).eq('id', tariff_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_tariff(tariff_id: str) -> bool:
        """Delete a tariff"""
        supabase.table('tariffs').delete().eq('id', tariff_id).execute()
        return True
    
    # ==================== SETTINGS ====================
    
    @staticmethod
    def get_settings() -> Optional[Dict]:
        """Get system settings"""
        result = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
        if result.data:
            return result.data[0].get('data', {})
        return {'currency': 'USD'}
    
    @staticmethod
    def update_settings(settings_data: Dict) -> Dict:
        """Update system settings"""
        # Check if exists
        existing = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
        if existing.data:
            result = supabase.table('settings').update({
                'currency': settings_data.get('currency', 'USD'),
                'data': settings_data
            }).eq('key', 'system').execute()
        else:
            result = supabase.table('settings').insert({
                'key': 'system',
                'currency': settings_data.get('currency', 'USD'),
                'data': settings_data
            }).execute()
        return result.data[0] if result.data else settings_data
    
    # ==================== ACTIVITY LOG ====================
    
    @staticmethod
    def get_activity_log(limit: int = 100) -> List[Dict]:
        """Get activity log"""
        result = supabase.table('activity_log').select('*').order('created_at', desc=True).limit(limit).execute()
        return result.data
    
    @staticmethod
    def create_activity_log(log_data: Dict) -> Dict:
        """Create activity log entry"""
        result = supabase.table('activity_log').insert(log_data).execute()
        return result.data[0] if result.data else None
    
    # ==================== AUDIO FILES ====================
    
    @staticmethod
    def get_audio_by_client(client_id: str) -> List[Dict]:
        """Get audio files for a client"""
        result = supabase.table('audio_files').select('*').eq('client_id', client_id).order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def get_audio_by_id(audio_id: str) -> Optional[Dict]:
        """Get audio file by ID"""
        result = supabase.table('audio_files').select('*').eq('id', audio_id).limit(1).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def create_audio(audio_data: Dict) -> Dict:
        """Create audio file record"""
        result = supabase.table('audio_files').insert(audio_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def delete_audio(audio_id: str) -> bool:
        """Delete audio file record"""
        supabase.table('audio_files').delete().eq('id', audio_id).execute()
        return True
    
    # ==================== NOTIFICATIONS ====================
    
    @staticmethod
    def get_notifications(user_id: str) -> List[Dict]:
        """Get notifications for a user"""
        result = supabase.table('notifications').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data
    
    @staticmethod
    def count_unread_notifications(user_id: str) -> int:
        """Count unread notifications"""
        result = supabase.table('notifications').select('count', count='exact').eq('user_id', user_id).eq('is_read', False).execute()
        return result.count or 0
    
    @staticmethod
    def create_notification(notification_data: Dict) -> Dict:
        """Create a notification"""
        result = supabase.table('notifications').insert(notification_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def mark_notification_read(notification_id: str) -> Dict:
        """Mark notification as read"""
        result = supabase.table('notifications').update({'is_read': True}).eq('id', notification_id).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    def mark_all_notifications_read(user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        supabase.table('notifications').update({'is_read': True}).eq('user_id', user_id).eq('is_read', False).execute()
        return True


# Export singleton instance
db = SupabaseDB()
