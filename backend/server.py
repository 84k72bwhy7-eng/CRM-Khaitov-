"""
SchoolCRM Backend API - Supabase Version
=========================================
FastAPI backend with Supabase PostgreSQL database
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from supabase import create_client, Client
import os
import io
import csv
import json
import hmac
import hashlib
from urllib.parse import parse_qs
import time
import asyncio
import httpx
import uuid

# Load environment variables
load_dotenv()

# App initialization
app = FastAPI(title="SchoolCRM API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
JWT_SECRET = os.environ.get("JWT_SECRET", "crm_secure_jwt_secret_key_2024")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://crmtelegram-app.preview.emergentagent.com")
# Telegram Mini App URL - should be the URL configured in BotFather
TELEGRAM_MINIAPP_URL = os.environ.get("TELEGRAM_MINIAPP_URL", WEBAPP_URL)

# Environment mode
APP_ENV = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"
DISABLE_SEED = os.environ.get("DISABLE_SEED", "false").lower() == "true" or IS_PRODUCTION

# Supabase connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"[App] Environment: {APP_ENV}")
print(f"[App] Database: Supabase PostgreSQL")
print(f"[App] Seeding disabled: {DISABLE_SEED}")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Upload directory
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== PYDANTIC MODELS ====================

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    role: str = "manager"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ClientCreate(BaseModel):
    name: str
    phone: str
    source: Optional[str] = ""
    manager_id: Optional[str] = None
    status: str = "new"
    is_lead: bool = True
    tariff_id: Optional[str] = None
    group_id: Optional[str] = None
    initial_comment: Optional[str] = None
    reminder_text: Optional[str] = None
    reminder_at: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None
    is_lead: Optional[bool] = None
    is_archived: Optional[bool] = None
    tariff_id: Optional[str] = None
    group_id: Optional[str] = None

class NoteCreate(BaseModel):
    client_id: str
    text: str

class PaymentCreate(BaseModel):
    client_id: str
    amount: float
    currency: str = "USD"
    status: str = "pending"
    date: Optional[str] = None
    comment: Optional[str] = None

class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None
    comment: Optional[str] = None

class ReminderCreate(BaseModel):
    client_id: str
    text: str
    remind_at: str

class ReminderUpdate(BaseModel):
    text: Optional[str] = None
    remind_at: Optional[str] = None
    is_completed: Optional[bool] = None

class StatusCreate(BaseModel):
    name: str
    color: str = "#3B82F6"
    order: int = 0

class StatusUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None

class TariffCreate(BaseModel):
    name: str
    price: float
    currency: str = "USD"
    description: Optional[str] = ""

class TariffUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None

class GroupCreate(BaseModel):
    name: str
    color: Optional[str] = "#6B7280"
    description: Optional[str] = ""

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

class SettingsUpdate(BaseModel):
    currency: Optional[str] = None

class TelegramAuthRequest(BaseModel):
    initData: str

class TelegramLinkRequest(BaseModel):
    email: str
    password: str
    initData: str

class AdminTelegramLink(BaseModel):
    telegram_id: str
    telegram_username: Optional[str] = ""

# ==================== HELPER FUNCTIONS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def new_uuid() -> str:
    return str(uuid.uuid4())

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="User not found")
    
    user = result.data[0]
    del user['password']
    return user

def log_activity(user_id: str, user_name: str, action: str, entity_type: str, entity_id: str, details: dict = None):
    """Log activity for audit trail"""
    supabase.table('activity_log').insert({
        'id': new_uuid(),
        'user_id': user_id,
        'user_name': user_name,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'details': details or {},
        'created_at': datetime.now(timezone.utc).isoformat()
    }).execute()

def get_system_currency():
    """Get the system currency setting"""
    result = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
    if result.data:
        data = result.data[0].get('data', {})
        return data.get('currency', 'USD') if isinstance(data, dict) else 'USD'
    return "USD"

# ==================== TELEGRAM NOTIFICATION SYSTEM ====================

async def send_telegram_message(chat_id: str, text: str, reply_markup: dict = None):
    """Send a message via Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_reminder_message(client_name: str, client_phone: str, reminder_text: str, remind_at: str, client_id: str) -> tuple:
    """Format reminder message for Telegram with Mini App button"""
    try:
        dt = datetime.fromisoformat(remind_at.replace('Z', '+00:00'))
        formatted_time = dt.strftime("%d.%m.%Y %H:%M")
    except:
        formatted_time = remind_at
    
    message = f"""🔔 <b>Eslatma!</b>

👤 <b>Mijoz:</b> {client_name}
📞 <b>Telefon:</b> <code>{client_phone}</code>
📝 <b>Eslatma:</b> {reminder_text}
⏰ <b>Vaqt:</b> {formatted_time}

<i>Telefon raqamini bosib nusxalang va qo'ng'iroq qiling</i>"""
    
    # Use web_app button to open Mini App inside Telegram
    # Pass client_id as URL parameter for deep linking
    miniapp_url = f"{TELEGRAM_MINIAPP_URL}/clients/{client_id}"
    
    reply_markup = {
        "inline_keyboard": [[
            {
                "text": "📱 CRM da ochish",
                "web_app": {"url": miniapp_url}
            }
        ]]
    }
    return message, reply_markup

async def check_and_send_telegram_reminders():
    """Background task to check and send Telegram reminders"""
    print(f"[{datetime.now().isoformat()}] Checking for due reminders...")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Find due reminders that haven't been sent
    result = supabase.table('reminders').select('*').lt('remind_at', now).eq('is_completed', False).eq('telegram_sent', False).execute()
    due_reminders = result.data or []
    
    sent_count = 0
    for reminder in due_reminders:
        # Get user
        user_result = supabase.table('users').select('*').eq('id', reminder['user_id']).limit(1).execute()
        if not user_result.data:
            continue
        user = user_result.data[0]
        
        telegram_id = user.get('telegram_id')
        if not telegram_id:
            supabase.table('reminders').update({
                'telegram_sent': True,
                'telegram_sent_at': now,
                'telegram_success': False
            }).eq('id', reminder['id']).execute()
            continue
        
        # Get client
        client_result = supabase.table('clients').select('*').eq('id', reminder['client_id']).limit(1).execute()
        if not client_result.data:
            continue
        client = client_result.data[0]
        
        message, reply_markup = format_reminder_message(
            client.get('name', 'Unknown'),
            client.get('phone', 'N/A'),
            reminder.get('text', ''),
            reminder.get('remind_at', ''),
            client['id']
        )
        
        success = await send_telegram_message(telegram_id, message, reply_markup)
        
        supabase.table('reminders').update({
            'telegram_sent': True,
            'telegram_sent_at': datetime.now(timezone.utc).isoformat(),
            'telegram_success': success
        }).eq('id', reminder['id']).execute()
        
        if success:
            sent_count += 1
            print(f"  ✓ Sent reminder to {user.get('name')}")
    
    if sent_count > 0:
        print(f"[{datetime.now().isoformat()}] Sent {sent_count} Telegram reminder(s)")
    return sent_count

# Background scheduler
reminder_scheduler_running = False

async def reminder_scheduler_loop():
    """Background loop that checks reminders every minute"""
    global reminder_scheduler_running
    reminder_scheduler_running = True
    print("[Reminder Scheduler] Started")
    
    while reminder_scheduler_running:
        try:
            await check_and_send_telegram_reminders()
        except Exception as e:
            print(f"[Reminder Scheduler] Error: {e}")
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    print("[App] Starting reminder scheduler...")
    asyncio.create_task(reminder_scheduler_loop())

# ==================== TELEGRAM AUTH ====================

def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData"""
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")
    
    try:
        parsed = dict(parse_qs(init_data, keep_blank_values=True))
        parsed = {k: v[0] for k, v in parsed.items()}
    except Exception:
        raise ValueError("Invalid initData format")
    
    received_hash = parsed.pop('hash', None)
    if not received_hash:
        raise ValueError("Hash not found")
    
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid hash")
    
    auth_date = int(parsed.get('auth_date', 0))
    if time.time() - auth_date > 86400:
        raise ValueError("Auth data expired")
    
    user_json = parsed.get('user', '{}')
    try:
        user_data = json.loads(user_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid user data")
    
    return user_data

# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "SchoolCRM",
        "version": "4.0.0",
        "environment": APP_ENV,
        "database": "Supabase PostgreSQL",
        "seed_disabled": DISABLE_SEED
    }

@app.get("/api/admin/database-status")
async def database_status(current_user: dict = Depends(get_current_user)):
    """Admin: Get database status"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    counts = {}
    for table in ['users', 'clients', 'payments', 'reminders', 'notes', 'statuses', 'groups', 'tariffs']:
        result = supabase.table(table).select('count', count='exact').execute()
        counts[table] = result.count or 0
    
    return {
        "environment": APP_ENV,
        "is_production": IS_PRODUCTION,
        "database": "Supabase PostgreSQL",
        "seed_disabled": DISABLE_SEED,
        "collections": counts,
        "protection_status": "ENABLED" if DISABLE_SEED else "DISABLED"
    }

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/login")
async def login(data: UserLogin):
    result = supabase.table('users').select('*').eq('email', data.email).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = result.data[0]
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    del user["password"]
    return {"token": token, "user": user}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.put("/api/auth/profile")
async def update_profile(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    if update_data:
        supabase.table('users').update(update_data).eq('id', current_user["id"]).execute()
        log_activity(current_user["id"], current_user["name"], "update", "user", current_user["id"], {"fields": list(update_data.keys())})
    
    result = supabase.table('users').select('*').eq('id', current_user["id"]).limit(1).execute()
    user = result.data[0]
    del user["password"]
    return user

@app.post("/api/auth/telegram")
async def telegram_auth(data: TelegramAuthRequest):
    """Authenticate user via Telegram WebApp"""
    try:
        tg_user = validate_telegram_init_data(data.initData, TELEGRAM_BOT_TOKEN)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    telegram_id = str(tg_user.get('id'))
    if not telegram_id:
        raise HTTPException(status_code=401, detail="No Telegram user ID")
    
    result = supabase.table('users').select('*').eq('telegram_id', telegram_id).limit(1).execute()
    
    if not result.data:
        return {
            "status": "not_linked",
            "telegram_user": {
                "id": telegram_id,
                "first_name": tg_user.get('first_name', ''),
                "last_name": tg_user.get('last_name', ''),
                "username": tg_user.get('username', '')
            },
            "message": "Telegram account not linked to CRM user"
        }
    
    user = result.data[0]
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    del user["password"]
    
    return {"status": "success", "token": token, "user": user}

@app.post("/api/auth/telegram/link")
async def link_telegram_account(data: TelegramLinkRequest):
    """Link existing CRM account to Telegram"""
    try:
        tg_user = validate_telegram_init_data(data.initData, TELEGRAM_BOT_TOKEN)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Telegram validation failed: {str(e)}")
    
    telegram_id = str(tg_user.get('id'))
    
    result = supabase.table('users').select('*').eq('email', data.email).limit(1).execute()
    if not result.data or not verify_password(data.password, result.data[0]["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = result.data[0]
    
    existing = supabase.table('users').select('*').eq('telegram_id', telegram_id).limit(1).execute()
    if existing.data and existing.data[0]["id"] != user["id"]:
        raise HTTPException(status_code=400, detail="Telegram account already linked to another user")
    
    supabase.table('users').update({
        'telegram_id': telegram_id,
        'telegram_username': tg_user.get('username', ''),
        'telegram_first_name': tg_user.get('first_name', ''),
        'telegram_linked_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', user["id"]).execute()
    
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    
    result = supabase.table('users').select('*').eq('id', user["id"]).limit(1).execute()
    user = result.data[0]
    del user["password"]
    
    log_activity(user["id"], user["name"], "link_telegram", "user", user["id"], {"telegram_id": telegram_id})
    
    return {"status": "success", "token": token, "user": user}

@app.delete("/api/users/{user_id}/telegram")
async def admin_unlink_telegram(user_id: str, current_user: dict = Depends(get_current_user)):
    """Admin: Unlink Telegram account"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = result.data[0]
    if not user.get("telegram_id"):
        raise HTTPException(status_code=400, detail="User has no linked Telegram account")
    
    old_telegram_id = user.get("telegram_id")
    
    supabase.table('users').update({
        'telegram_id': None,
        'telegram_username': None,
        'telegram_first_name': None,
        'telegram_linked_at': None
    }).eq('id', user_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "unlink_telegram", "user", user_id,
                {"telegram_id": old_telegram_id, "user_name": user.get("name")})
    
    return {"message": f"Telegram account unlinked from {user.get('name')}"}

@app.post("/api/users/{user_id}/telegram")
async def admin_link_telegram(user_id: str, data: AdminTelegramLink, current_user: dict = Depends(get_current_user)):
    """Admin: Manually link Telegram"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = supabase.table('users').select('*').eq('telegram_id', data.telegram_id).limit(1).execute()
    if existing.data and existing.data[0]["id"] != user_id:
        raise HTTPException(status_code=400, detail=f"Telegram ID already linked to: {existing.data[0].get('name')}")
    
    supabase.table('users').update({
        'telegram_id': data.telegram_id,
        'telegram_username': data.telegram_username,
        'telegram_linked_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', user_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "admin_link_telegram", "user", user_id,
                {"telegram_id": data.telegram_id})
    
    return {"message": f"Telegram account linked to {result.data[0].get('name')}"}

# ==================== USERS ENDPOINTS ====================

@app.get("/api/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = supabase.table('users').select('*').order('created_at', desc=True).execute()
    users = []
    for u in result.data:
        del u['password']
        users.append(u)
    return users

@app.post("/api/users")
async def create_user(data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = supabase.table('users').select('*').eq('email', data.email).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user_id = new_uuid()
    user_doc = {
        'id': user_id,
        'name': data.name,
        'email': data.email,
        'phone': data.phone,
        'password': get_password_hash(data.password),
        'role': data.role,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('users').insert(user_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "user", user_id, {"email": data.email})
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    user = result.data[0]
    del user['password']
    return user

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    if update_data:
        supabase.table('users').update(update_data).eq('id', user_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "user", user_id, {"fields": list(update_data.keys())})
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = result.data[0]
    del user['password']
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = supabase.table('users').select('*').eq('id', user_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    supabase.table('users').delete().eq('id', user_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "user", user_id, {})
    return {"message": "User deleted"}

# ==================== TARIFFS ENDPOINTS ====================

@app.get("/api/tariffs")
async def get_tariffs(current_user: dict = Depends(get_current_user)):
    result = supabase.table('tariffs').select('*').order('created_at', desc=True).execute()
    return result.data

@app.post("/api/tariffs")
async def create_tariff(data: TariffCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tariff_id = new_uuid()
    tariff_doc = {
        'id': tariff_id,
        'name': data.name,
        'price': data.price,
        'currency': data.currency,
        'description': data.description,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('tariffs').insert(tariff_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "tariff", tariff_id, {"name": data.name})
    
    result = supabase.table('tariffs').select('*').eq('id', tariff_id).limit(1).execute()
    return result.data[0]

@app.put("/api/tariffs/{tariff_id}")
async def update_tariff(tariff_id: str, data: TariffUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        supabase.table('tariffs').update(update_data).eq('id', tariff_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "tariff", tariff_id, update_data)
    
    result = supabase.table('tariffs').select('*').eq('id', tariff_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return result.data[0]

@app.delete("/api/tariffs/{tariff_id}")
async def delete_tariff(tariff_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if in use
    clients = supabase.table('clients').select('count', count='exact').eq('tariff_id', tariff_id).execute()
    if clients.count > 0:
        raise HTTPException(status_code=400, detail="Tariff is in use by clients")
    
    result = supabase.table('tariffs').select('*').eq('id', tariff_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tariff not found")
    
    supabase.table('tariffs').delete().eq('id', tariff_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "tariff", tariff_id, {})
    return {"message": "Tariff deleted"}

# ==================== GROUPS ENDPOINTS ====================

@app.get("/api/groups")
async def get_groups(current_user: dict = Depends(get_current_user)):
    result = supabase.table('groups').select('*').order('name').execute()
    return result.data

@app.post("/api/groups")
async def create_group(data: GroupCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = supabase.table('groups').select('*').eq('name', data.name).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    
    group_id = new_uuid()
    group_doc = {
        'id': group_id,
        'name': data.name,
        'color': data.color or "#6B7280",
        'description': data.description or "",
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('groups').insert(group_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "group", group_id, {"name": data.name})
    
    result = supabase.table('groups').select('*').eq('id', group_id).limit(1).execute()
    return result.data[0]

@app.put("/api/groups/{group_id}")
async def update_group(group_id: str, data: GroupUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        supabase.table('groups').update(update_data).eq('id', group_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "group", group_id, update_data)
    
    result = supabase.table('groups').select('*').eq('id', group_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Group not found")
    return result.data[0]

@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    clients = supabase.table('clients').select('count', count='exact').eq('group_id', group_id).execute()
    if clients.count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete group: {clients.count} clients are using it")
    
    result = supabase.table('groups').select('*').eq('id', group_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Group not found")
    
    supabase.table('groups').delete().eq('id', group_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "group", group_id, {})
    return {"message": "Group deleted"}

# ==================== SETTINGS ENDPOINTS ====================

@app.get("/api/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    result = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
    if result.data:
        return result.data[0].get('data', {'currency': 'USD'})
    return {"currency": "USD"}

@app.put("/api/settings")
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        existing = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
        if existing.data:
            supabase.table('settings').update({
                'currency': update_data.get('currency', 'USD'),
                'data': update_data
            }).eq('key', 'system').execute()
        else:
            supabase.table('settings').insert({
                'id': new_uuid(),
                'key': 'system',
                'currency': update_data.get('currency', 'USD'),
                'data': update_data
            }).execute()
        log_activity(current_user["id"], current_user["name"], "update", "settings", "system", update_data)
    
    result = supabase.table('settings').select('*').eq('key', 'system').limit(1).execute()
    return result.data[0].get('data', {'currency': 'USD'}) if result.data else {'currency': 'USD'}

# ==================== CLIENTS ENDPOINTS ====================

@app.get("/api/clients")
async def get_clients(
    search: Optional[str] = None,
    status: Optional[str] = None,
    group_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    is_archived: Optional[bool] = False,
    exclude_sold: Optional[bool] = False,
    current_user: dict = Depends(get_current_user)
):
    query = supabase.table('clients').select('*')
    
    if is_archived:
        query = query.eq('archived', True)
    else:
        query = query.eq('archived', False)
    
    if current_user["role"] != "admin":
        query = query.eq('manager_id', current_user["id"])
    
    if search:
        query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%")
    
    if status:
        query = query.eq('status', status)
    elif exclude_sold:
        query = query.neq('status', 'sold')
    
    if group_id:
        query = query.eq('group_id', group_id)
    
    if date_from:
        query = query.gte('created_at', date_from)
    if date_to:
        query = query.lte('created_at', date_to)
    
    result = query.order('created_at', desc=True).execute()
    clients = result.data or []
    
    # Enrich with related data
    tariffs = {t['id']: t for t in supabase.table('tariffs').select('*').execute().data}
    groups = {g['id']: g for g in supabase.table('groups').select('*').execute().data}
    users = {u['id']: u for u in supabase.table('users').select('id,name').execute().data}
    
    for client in clients:
        if client.get('tariff_id') and client['tariff_id'] in tariffs:
            client['tariff_name'] = tariffs[client['tariff_id']]['name']
            client['tariff_price'] = tariffs[client['tariff_id']]['price']
        if client.get('group_id') and client['group_id'] in groups:
            client['group_name'] = groups[client['group_id']]['name']
            client['group_color'] = groups[client['group_id']]['color']
        if client.get('manager_id') and client['manager_id'] in users:
            client['manager_name'] = users[client['manager_id']]['name']
    
    return clients

@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = result.data[0]
    
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if client.get('tariff_id'):
        tariff = supabase.table('tariffs').select('*').eq('id', client['tariff_id']).limit(1).execute()
        if tariff.data:
            client['tariff_name'] = tariff.data[0]['name']
            client['tariff_price'] = tariff.data[0]['price']
    
    return client

@app.post("/api/clients")
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    # Check duplicate phone - allow duplicates for now (different from MongoDB version)
    # existing = supabase.table('clients').select('*').eq('phone', data.phone).limit(1).execute()
    # if existing.data:
    #     raise HTTPException(status_code=400, detail="Phone number already exists")
    
    client_id = new_uuid()
    client_doc = {
        'id': client_id,
        'name': data.name,
        'phone': data.phone,
        'source': data.source,
        'manager_id': data.manager_id or current_user["id"],
        'status': data.status,
        'is_lead': data.is_lead,
        'archived': False,
        'tariff_id': data.tariff_id,
        'group_id': data.group_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('clients').insert(client_doc).execute()
    
    # Create initial comment
    if data.initial_comment:
        supabase.table('notes').insert({
            'id': new_uuid(),
            'client_id': client_id,
            'user_id': current_user["id"],
            'text': data.initial_comment,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
    
    # Create reminder
    if data.reminder_text and data.reminder_at:
        manager_id = data.manager_id or current_user["id"]
        supabase.table('reminders').insert({
            'id': new_uuid(),
            'client_id': client_id,
            'user_id': manager_id,
            'text': data.reminder_text,
            'remind_at': data.reminder_at,
            'is_completed': False,
            'telegram_sent': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
    
    log_activity(current_user["id"], current_user["name"], "create", "client", client_id, {"name": data.name})
    
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    return result.data[0]

@app.put("/api/clients/{client_id}")
async def update_client(client_id: str, data: ClientUpdate, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = result.data[0]
    
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    # Map is_archived to archived
    if 'is_archived' in update_data:
        update_data['archived'] = update_data.pop('is_archived')
    
    old_status = client.get("status")
    
    if update_data:
        supabase.table('clients').update(update_data).eq('id', client_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "client", client_id,
                    {"fields": list(update_data.keys()), "old_status": old_status, "new_status": update_data.get("status")})
    
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    return result.data[0]

@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = result.data[0]
    
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete related records
    supabase.table('notes').delete().eq('client_id', client_id).execute()
    supabase.table('payments').delete().eq('client_id', client_id).execute()
    supabase.table('reminders').delete().eq('client_id', client_id).execute()
    supabase.table('clients').delete().eq('id', client_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "delete", "client", client_id, {"name": client.get("name")})
    return {"message": "Client deleted"}

@app.post("/api/clients/{client_id}/archive")
async def archive_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    supabase.table('clients').update({
        'archived': True,
        'archived_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', client_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "archive", "client", client_id, {"name": result.data[0].get("name")})
    return {"message": "Client archived"}

@app.post("/api/clients/{client_id}/restore")
async def restore_client(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    supabase.table('clients').update({
        'archived': False,
        'archived_at': None
    }).eq('id', client_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "restore", "client", client_id, {"name": result.data[0].get("name")})
    return {"message": "Client restored"}

@app.post("/api/clients/{client_id}/convert-to-lead")
async def convert_to_lead(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('clients').select('*').eq('id', client_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    supabase.table('clients').update({
        'is_lead': True,
        'status': 'new'
    }).eq('id', client_id).execute()
    
    log_activity(current_user["id"], current_user["name"], "convert_to_lead", "client", client_id, {"name": result.data[0].get("name")})
    return {"message": "Client converted to lead"}

# ==================== IMPORT ENDPOINTS ====================

@app.post("/api/import/preview")
async def import_preview(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Preview import data"""
    content = await file.read()
    rows = []
    errors = []
    
    try:
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        for i, row in enumerate(reader):
            if not row.get('name') or not row.get('phone'):
                errors.append(f"Row {i+1}: Missing name or phone")
                continue
            rows.append({
                "name": row.get('name', '').strip(),
                "phone": row.get('phone', '').strip(),
                "source": row.get('source', '').strip(),
                "status": row.get('status', 'new').strip()
            })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
    
    return {"rows": rows, "errors": errors, "total": len(rows)}

@app.post("/api/import/save")
async def import_save(rows: List[dict], current_user: dict = Depends(get_current_user)):
    """Save imported data"""
    created = 0
    errors = []
    
    for i, row in enumerate(rows):
        try:
            client_id = new_uuid()
            supabase.table('clients').insert({
                'id': client_id,
                'name': row.get('name'),
                'phone': row.get('phone'),
                'source': row.get('source', ''),
                'status': row.get('status', 'new'),
                'manager_id': row.get('manager_id') or current_user["id"],
                'is_lead': True,
                'archived': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            created += 1
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    log_activity(current_user["id"], current_user["name"], "import", "client", "batch", {"created": created})
    return {"created": created, "errors": errors}

# ==================== NOTES ENDPOINTS ====================

@app.get("/api/notes/{client_id}")
async def get_notes(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('notes').select('*').eq('client_id', client_id).order('created_at', desc=True).execute()
    return result.data

@app.post("/api/notes")
async def create_note(data: NoteCreate, current_user: dict = Depends(get_current_user)):
    note_id = new_uuid()
    note_doc = {
        'id': note_id,
        'client_id': data.client_id,
        'user_id': current_user["id"],
        'text': data.text,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('notes').insert(note_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "note", note_id, {"client_id": data.client_id})
    
    result = supabase.table('notes').select('*').eq('id', note_id).limit(1).execute()
    return result.data[0]

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('notes').select('*').eq('id', note_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Note not found")
    
    supabase.table('notes').delete().eq('id', note_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "note", note_id, {})
    return {"message": "Note deleted"}

# ==================== PAYMENTS ENDPOINTS ====================

@app.get("/api/payments")
async def get_payments(current_user: dict = Depends(get_current_user)):
    result = supabase.table('payments').select('*').order('payment_date', desc=True).execute()
    return result.data

@app.get("/api/payments/client/{client_id}")
async def get_client_payments(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('payments').select('*').eq('client_id', client_id).order('payment_date', desc=True).execute()
    return result.data

@app.post("/api/payments")
async def create_payment(data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    payment_id = new_uuid()
    payment_doc = {
        'id': payment_id,
        'client_id': data.client_id,
        'user_id': current_user["id"],
        'amount': data.amount,
        'currency': data.currency,
        'status': data.status,
        'payment_date': data.date or datetime.now(timezone.utc).isoformat(),
        'comment': data.comment,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('payments').insert(payment_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "payment", payment_id, {"amount": data.amount, "client_id": data.client_id})
    
    result = supabase.table('payments').select('*').eq('id', payment_id).limit(1).execute()
    return result.data[0]

@app.put("/api/payments/{payment_id}")
async def update_payment(payment_id: str, data: PaymentUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if 'date' in update_data:
        update_data['payment_date'] = update_data.pop('date')
    
    if update_data:
        supabase.table('payments').update(update_data).eq('id', payment_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "payment", payment_id, update_data)
    
    result = supabase.table('payments').select('*').eq('id', payment_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result.data[0]

@app.delete("/api/payments/{payment_id}")
async def delete_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('payments').select('*').eq('id', payment_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    supabase.table('payments').delete().eq('id', payment_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "payment", payment_id, {})
    return {"message": "Payment deleted"}

# ==================== REMINDERS ENDPOINTS ====================

@app.get("/api/reminders")
async def get_reminders(current_user: dict = Depends(get_current_user)):
    query = supabase.table('reminders').select('*')
    if current_user["role"] != "admin":
        query = query.eq('user_id', current_user["id"])
    result = query.order('remind_at').execute()
    return result.data

@app.get("/api/reminders/overdue")
async def get_overdue_reminders(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    query = supabase.table('reminders').select('*').lt('remind_at', now).eq('is_completed', False)
    if current_user["role"] != "admin":
        query = query.eq('user_id', current_user["id"])
    result = query.order('remind_at').execute()
    return result.data

@app.post("/api/reminders")
async def create_reminder(data: ReminderCreate, current_user: dict = Depends(get_current_user)):
    reminder_id = new_uuid()
    reminder_doc = {
        'id': reminder_id,
        'client_id': data.client_id,
        'user_id': current_user["id"],
        'text': data.text,
        'remind_at': data.remind_at,
        'is_completed': False,
        'telegram_sent': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('reminders').insert(reminder_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "reminder", reminder_id, {"client_id": data.client_id})
    
    result = supabase.table('reminders').select('*').eq('id', reminder_id).limit(1).execute()
    return result.data[0]

@app.put("/api/reminders/{reminder_id}")
async def update_reminder(reminder_id: str, data: ReminderUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        supabase.table('reminders').update(update_data).eq('id', reminder_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "reminder", reminder_id, update_data)
    
    result = supabase.table('reminders').select('*').eq('id', reminder_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return result.data[0]

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('reminders').select('*').eq('id', reminder_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    supabase.table('reminders').delete().eq('id', reminder_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "reminder", reminder_id, {})
    return {"message": "Reminder deleted"}

# ==================== NOTIFICATIONS ENDPOINTS ====================

@app.get("/api/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    result = supabase.table('notifications').select('*').eq('user_id', current_user["id"]).order('created_at', desc=True).execute()
    return result.data

@app.get("/api/notifications/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    result = supabase.table('notifications').select('count', count='exact').eq('user_id', current_user["id"]).eq('is_read', False).execute()
    return {"count": result.count or 0}

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    supabase.table('notifications').update({'is_read': True}).eq('id', notification_id).execute()
    return {"message": "Notification marked as read"}

@app.put("/api/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    supabase.table('notifications').update({'is_read': True}).eq('user_id', current_user["id"]).eq('is_read', False).execute()
    return {"message": "All notifications marked as read"}

@app.get("/api/notifications/check-reminders")
async def check_reminders(current_user: dict = Depends(get_current_user)):
    """Check for due reminders"""
    now = datetime.now(timezone.utc).isoformat()
    result = supabase.table('reminders').select('*').eq('user_id', current_user["id"]).lt('remind_at', now).eq('is_completed', False).eq('notified', False).execute()
    
    due_reminders = result.data or []
    for reminder in due_reminders:
        client = supabase.table('clients').select('name').eq('id', reminder['client_id']).limit(1).execute()
        client_name = client.data[0]['name'] if client.data else 'Unknown'
        
        supabase.table('notifications').insert({
            'id': new_uuid(),
            'user_id': current_user["id"],
            'type': 'reminder',
            'title': 'Reminder Due',
            'message': f"Reminder for {client_name}: {reminder['text']}",
            'entity_type': 'reminder',
            'entity_id': reminder['id'],
            'is_read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        supabase.table('reminders').update({'notified': True}).eq('id', reminder['id']).execute()
    
    return {"checked": len(due_reminders)}

@app.post("/api/notifications/send-telegram-reminders")
async def send_telegram_reminders_manual(current_user: dict = Depends(get_current_user)):
    """Manually trigger Telegram reminder sending"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    sent = await check_and_send_telegram_reminders()
    return {"sent": sent}

@app.post("/api/notifications/test-telegram")
async def test_telegram(current_user: dict = Depends(get_current_user)):
    """Test Telegram notification"""
    telegram_id = current_user.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Your account has no linked Telegram")
    
    success = await send_telegram_message(
        telegram_id,
        f"🔔 <b>Test Notification</b>\n\nHello {current_user['name']}! This is a test message from SchoolCRM."
    )
    
    return {"success": success, "telegram_id": telegram_id}

@app.get("/api/notifications/telegram-status")
async def telegram_status(current_user: dict = Depends(get_current_user)):
    """Get Telegram notification system status"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count users with Telegram linked
    linked_result = supabase.table('users').select('count', count='exact').neq('telegram_id', None).execute()
    linked_users = linked_result.count or 0
    
    # Count pending reminders
    now = datetime.now(timezone.utc).isoformat()
    pending_result = supabase.table('reminders').select('count', count='exact').lt('remind_at', now).eq('is_completed', False).eq('telegram_sent', False).execute()
    pending_reminders = pending_result.count or 0
    
    # Recent sent
    sent_result = supabase.table('reminders').select('count', count='exact').eq('telegram_sent', True).execute()
    total_sent = sent_result.count or 0
    
    return {
        "scheduler_running": reminder_scheduler_running,
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
        "linked_users": linked_users,
        "pending_reminders": pending_reminders,
        "total_sent": total_sent
    }

# ==================== STATUSES ENDPOINTS ====================

@app.get("/api/statuses")
async def get_statuses(current_user: dict = Depends(get_current_user)):
    result = supabase.table('statuses').select('*').order('sort_order').execute()
    return result.data

@app.post("/api/statuses")
async def create_status(data: StatusCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = supabase.table('statuses').select('*').eq('name', data.name).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Status with this name already exists")
    
    status_id = new_uuid()
    status_doc = {
        'id': status_id,
        'name': data.name,
        'color': data.color,
        'sort_order': data.order,
        'is_default': False,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('statuses').insert(status_doc).execute()
    log_activity(current_user["id"], current_user["name"], "create", "status", status_id, {"name": data.name})
    
    result = supabase.table('statuses').select('*').eq('id', status_id).limit(1).execute()
    return result.data[0]

@app.put("/api/statuses/{status_id}")
async def update_status(status_id: str, data: StatusUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if 'order' in update_data:
        update_data['sort_order'] = update_data.pop('order')
    
    if update_data:
        supabase.table('statuses').update(update_data).eq('id', status_id).execute()
        log_activity(current_user["id"], current_user["name"], "update", "status", status_id, update_data)
    
    result = supabase.table('statuses').select('*').eq('id', status_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Status not found")
    return result.data[0]

@app.delete("/api/statuses/{status_id}")
async def delete_status(status_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = supabase.table('statuses').select('*').eq('id', status_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Status not found")
    
    if result.data[0].get('is_default'):
        raise HTTPException(status_code=400, detail="Cannot delete default status")
    
    supabase.table('statuses').delete().eq('id', status_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "status", status_id, {})
    return {"message": "Status deleted"}

# ==================== ACTIVITY LOG ====================

@app.get("/api/activity-log")
async def get_activity_log(
    limit: int = 100,
    entity_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = supabase.table('activity_log').select('*')
    if entity_type:
        query = query.eq('entity_type', entity_type)
    result = query.order('created_at', desc=True).limit(limit).execute()
    return result.data

# ==================== AUDIO FILES ENDPOINTS ====================

@app.get("/api/audio/{client_id}")
async def get_client_audio_files(client_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('audio_files').select('*').eq('client_id', client_id).order('created_at', desc=True).execute()
    return result.data

@app.post("/api/audio/upload")
async def upload_audio(
    client_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    allowed_types = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3", "audio/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{client_id}_{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    audio_id = new_uuid()
    audio_doc = {
        'id': audio_id,
        'client_id': client_id,
        'user_id': current_user["id"],
        'filename': filename,
        'original_name': file.filename,
        'content_type': file.content_type,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    supabase.table('audio_files').insert(audio_doc).execute()
    log_activity(current_user["id"], current_user["name"], "upload", "audio", audio_id, {"client_id": client_id})
    
    result = supabase.table('audio_files').select('*').eq('id', audio_id).limit(1).execute()
    return result.data[0]

@app.get("/api/audio/file/{audio_id}")
async def get_audio_file(audio_id: str, token: Optional[str] = None):
    """Serve audio file"""
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    result = supabase.table('audio_files').select('*').eq('id', audio_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio = result.data[0]
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    file_size = os.path.getsize(filepath)
    
    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
    
    return StreamingResponse(
        iterfile(),
        media_type=audio["content_type"],
        headers={"Content-Length": str(file_size), "Accept-Ranges": "bytes", "Cache-Control": "no-cache"}
    )

@app.get("/api/audio/stream/{audio_id}")
async def stream_audio_public(audio_id: str, token: str):
    """Public audio streaming with token auth"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = supabase.table('audio_files').select('*').eq('id', audio_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio = result.data[0]
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    file_size = os.path.getsize(filepath)
    
    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
    
    return StreamingResponse(
        iterfile(),
        media_type=audio["content_type"],
        headers={"Content-Length": str(file_size), "Accept-Ranges": "bytes", "Cache-Control": "no-cache"}
    )

@app.delete("/api/audio/{audio_id}")
async def delete_audio(audio_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table('audio_files').select('*').eq('id', audio_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    audio = result.data[0]
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    supabase.table('audio_files').delete().eq('id', audio_id).execute()
    log_activity(current_user["id"], current_user["name"], "delete", "audio", audio_id, {"filename": audio["original_name"]})
    return {"message": "Audio deleted"}

# ==================== EXPORT ENDPOINTS ====================

@app.get("/api/export/clients")
async def export_clients(format: str = "csv", current_user: dict = Depends(get_current_user)):
    query = supabase.table('clients').select('*')
    if current_user["role"] != "admin":
        query = query.eq('manager_id', current_user["id"])
    result = query.order('created_at', desc=True).execute()
    clients = result.data or []
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Phone", "Source", "Status", "Created At", "Is Lead", "Is Archived"])
        for c in clients:
            writer.writerow([
                c.get("name", ""),
                c.get("phone", ""),
                c.get("source", ""),
                c.get("status", ""),
                c.get("created_at", ""),
                c.get("is_lead", False),
                c.get("archived", False)
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clients_export.csv"}
        )
    raise HTTPException(status_code=400, detail="Format not supported. Use: csv")

# ==================== DASHBOARD STATS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    # Build base query
    query = supabase.table('clients').select('*').eq('archived', False)
    if current_user["role"] != "admin":
        query = query.eq('manager_id', current_user["id"])
    result = query.execute()
    clients = result.data or []
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    total_clients = len(clients)
    todays_leads = len([c for c in clients if c.get('created_at', '').startswith(today)])
    new_count = len([c for c in clients if c.get('status') == 'new'])
    contacted_count = len([c for c in clients if c.get('status') == 'contacted'])
    sold_count = len([c for c in clients if c.get('status') == 'sold'])
    
    # Payment stats
    client_ids = [c['id'] for c in clients]
    if client_ids:
        payments = supabase.table('payments').select('*').in_('client_id', client_ids).execute().data or []
    else:
        payments = []
    
    total_paid = sum(p.get('amount', 0) for p in payments if p.get('status') == 'paid')
    total_pending = sum(p.get('amount', 0) for p in payments if p.get('status') == 'pending')
    
    # Overdue reminders
    now = datetime.now(timezone.utc).isoformat()
    overdue_result = supabase.table('reminders').select('count', count='exact').eq('user_id', current_user["id"]).lt('remind_at', now).eq('is_completed', False).execute()
    overdue_reminders = overdue_result.count or 0
    
    return {
        "total_clients": total_clients,
        "todays_leads": todays_leads,
        "new_count": new_count,
        "contacted_count": contacted_count,
        "sold_count": sold_count,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "overdue_reminders": overdue_reminders,
        "currency": get_system_currency()
    }

@app.get("/api/dashboard/recent-clients")
async def get_recent_clients(current_user: dict = Depends(get_current_user)):
    query = supabase.table('clients').select('*').eq('archived', False)
    if current_user["role"] != "admin":
        query = query.eq('manager_id', current_user["id"])
    result = query.order('created_at', desc=True).limit(5).execute()
    return result.data

@app.get("/api/dashboard/recent-notes")
async def get_recent_notes(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        notes_result = supabase.table('notes').select('*').order('created_at', desc=True).limit(5).execute()
    else:
        # Get user's client IDs
        clients = supabase.table('clients').select('id').eq('manager_id', current_user["id"]).execute().data or []
        client_ids = [c['id'] for c in clients]
        if client_ids:
            notes_result = supabase.table('notes').select('*').in_('client_id', client_ids).order('created_at', desc=True).limit(5).execute()
        else:
            return []
    
    notes = notes_result.data or []
    
    # Add client names
    client_ids = list(set(n['client_id'] for n in notes))
    if client_ids:
        clients = supabase.table('clients').select('id,name').in_('id', client_ids).execute().data or []
        client_map = {c['id']: c['name'] for c in clients}
        for note in notes:
            note['client_name'] = client_map.get(note['client_id'], 'Unknown')
    
    return notes

@app.get("/api/dashboard/manager-stats")
async def get_manager_stats(current_user: dict = Depends(get_current_user)):
    """Get sales statistics per manager (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    managers = supabase.table('users').select('id,name,role').execute().data or []
    clients = supabase.table('clients').select('id,manager_id,status').execute().data or []
    payments = supabase.table('payments').select('client_id,amount,status').execute().data or []
    
    # Group clients by manager
    manager_clients = {}
    for c in clients:
        mid = c.get('manager_id')
        if mid:
            if mid not in manager_clients:
                manager_clients[mid] = []
            manager_clients[mid].append(c)
    
    # Group payments by client
    client_payments = {}
    for p in payments:
        cid = p.get('client_id')
        if cid:
            if cid not in client_payments:
                client_payments[cid] = []
            client_payments[cid].append(p)
    
    result = []
    for manager in managers:
        manager_id = manager['id']
        manager_client_list = manager_clients.get(manager_id, [])
        client_ids = [c['id'] for c in manager_client_list]
        
        sold_count = len([c for c in manager_client_list if c.get('status') == 'sold'])
        
        total_revenue = 0
        for cid in client_ids:
            for p in client_payments.get(cid, []):
                if p.get('status') == 'paid':
                    total_revenue += p.get('amount', 0)
        
        result.append({
            "id": manager_id,
            "name": manager["name"],
            "role": manager["role"],
            "sold_count": sold_count,
            "total_revenue": total_revenue,
            "total_clients": len(client_ids)
        })
    
    return sorted(result, key=lambda x: x["total_revenue"], reverse=True)

@app.get("/api/dashboard/analytics")
async def get_analytics(months: int = 6, current_user: dict = Depends(get_current_user)):
    """Get monthly analytics data"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=months * 30)
    
    clients = supabase.table('clients').select('*').execute().data or []
    payments = supabase.table('payments').select('*').execute().data or []
    tariffs = supabase.table('tariffs').select('*').execute().data or []
    
    monthly_data = []
    current = start_date
    
    while current <= end_date:
        month_start = current.replace(day=1).strftime("%Y-%m")
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        sold_count = len([c for c in clients if c.get('status') == 'sold' and c.get('created_at', '').startswith(month_start)])
        
        revenue = sum(
            p.get('amount', 0)
            for p in payments
            if p.get('status') == 'paid' and (p.get('payment_date') or '').startswith(month_start)
        )
        
        new_leads = len([c for c in clients if c.get('created_at', '').startswith(month_start)])
        
        monthly_data.append({
            "month": month_start,
            "month_name": current.strftime("%b %Y"),
            "sold_count": sold_count,
            "revenue": revenue,
            "new_leads": new_leads
        })
        
        current = next_month
    
    # Sales by tariff
    tariff_stats = []
    for tariff in tariffs:
        count = len([c for c in clients if c.get('tariff_id') == tariff['id'] and c.get('status') == 'sold'])
        tariff_stats.append({
            "name": tariff["name"],
            "price": tariff["price"],
            "sold_count": count,
            "revenue": count * tariff["price"]
        })
    
    # Month-over-month changes
    if len(monthly_data) >= 2:
        curr = monthly_data[-1]
        prev = monthly_data[-2]
        revenue_change = curr["revenue"] - prev["revenue"]
        revenue_change_pct = ((curr["revenue"] - prev["revenue"]) / prev["revenue"] * 100) if prev["revenue"] > 0 else 0
        deals_change = curr["sold_count"] - prev["sold_count"]
        deals_change_pct = ((curr["sold_count"] - prev["sold_count"]) / prev["sold_count"] * 100) if prev["sold_count"] > 0 else 0
    else:
        revenue_change = revenue_change_pct = deals_change = deals_change_pct = 0
    
    return {
        "monthly_data": monthly_data,
        "tariff_stats": tariff_stats,
        "summary": {
            "total_revenue": sum(m["revenue"] for m in monthly_data),
            "total_deals": sum(m["sold_count"] for m in monthly_data),
            "total_leads": sum(m["new_leads"] for m in monthly_data),
            "revenue_change": revenue_change,
            "revenue_change_pct": round(revenue_change_pct, 1),
            "deals_change": deals_change,
            "deals_change_pct": round(deals_change_pct, 1)
        },
        "currency": get_system_currency()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
