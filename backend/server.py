from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId
import os
import io
import csv
import json
import hmac
import hashlib
from urllib.parse import parse_qs
import time

# App initialization
app = FastAPI(title="SchoolCRM API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "crm_db")
JWT_SECRET = os.environ.get("JWT_SECRET", "crm_secure_jwt_secret_key_2024")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
clients_collection = db["clients"]
notes_collection = db["notes"]
payments_collection = db["payments"]
reminders_collection = db["reminders"]
statuses_collection = db["statuses"]
activity_log_collection = db["activity_log"]
audio_files_collection = db["audio_files"]
tariffs_collection = db["tariffs"]
settings_collection = db["settings"]
notifications_collection = db["notifications"]
groups_collection = db["groups"]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Upload directory for files
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

class ImportRow(BaseModel):
    name: str
    phone: str
    source: Optional[str] = ""
    status: Optional[str] = "new"
    manager_id: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return serialize_doc(user)

def log_activity(user_id: str, user_name: str, action: str, entity_type: str, entity_id: str, details: dict = None):
    """Log activity for audit trail"""
    activity_log_collection.insert_one({
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    })

def create_notification(user_id: str, title: str, message: str, notification_type: str = "reminder", entity_id: str = None):
    """Create a notification for a user"""
    notifications_collection.insert_one({
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "entity_id": entity_id,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

def get_system_currency():
    """Get the system currency setting"""
    settings = settings_collection.find_one({"key": "system"})
    if settings:
        return settings.get("currency", "USD")
    return "USD"

# ==================== SEED DATA ====================

def seed_admin():
    admin = users_collection.find_one({"email": "admin@crm.local"})
    if not admin:
        users_collection.insert_one({
            "name": "Admin",
            "email": "admin@crm.local",
            "phone": "+998900000000",
            "password": get_password_hash("admin123"),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        print("Admin user created: admin@crm.local / admin123")

def seed_default_statuses():
    """Seed default statuses if none exist"""
    if statuses_collection.count_documents({}) == 0:
        default_statuses = [
            {"name": "new", "color": "#3B82F6", "order": 1, "is_default": True},
            {"name": "contacted", "color": "#F59E0B", "order": 2, "is_default": True},
            {"name": "sold", "color": "#22C55E", "order": 3, "is_default": True}
        ]
        statuses_collection.insert_many(default_statuses)
        print("Default statuses created")

def seed_default_settings():
    """Seed default system settings"""
    if not settings_collection.find_one({"key": "system"}):
        settings_collection.insert_one({
            "key": "system",
            "currency": "USD",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        print("Default settings created")

seed_admin()
seed_default_statuses()
seed_default_settings()

# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": "SchoolCRM", "version": "3.0.0"}

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/login")
async def login(data: UserLogin):
    user = users_collection.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    user_data = serialize_doc(user)
    del user_data["password"]
    return {"token": token, "user": user_data}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_data = {k: v for k, v in current_user.items() if k != "password"}
    return user_data

@app.put("/api/auth/profile")
async def update_profile(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    if update_data:
        users_collection.update_one({"_id": ObjectId(current_user["id"])}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "user", current_user["id"], {"fields": list(update_data.keys())})
    user = users_collection.find_one({"_id": ObjectId(current_user["id"])}, {"password": 0})
    return serialize_doc(user)

# ==================== USERS ENDPOINTS ====================

@app.get("/api/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    users = list(users_collection.find({}, {"password": 0}))
    return [serialize_doc(u) for u in users]

@app.post("/api/users")
async def create_user(data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user_doc = {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "password": get_password_hash(data.password),
        "role": data.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = users_collection.insert_one(user_doc)
    log_activity(current_user["id"], current_user["name"], "create", "user", str(result.inserted_id), {"email": data.email})
    user = users_collection.find_one({"_id": result.inserted_id}, {"password": 0})
    return serialize_doc(user)

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    if update_data:
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "user", user_id, {"fields": list(update_data.keys())})
    user = users_collection.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_doc(user)

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    log_activity(current_user["id"], current_user["name"], "delete", "user", user_id, {})
    return {"message": "User deleted"}

# ==================== TARIFFS ENDPOINTS ====================

@app.get("/api/tariffs")
async def get_tariffs(current_user: dict = Depends(get_current_user)):
    tariffs = list(tariffs_collection.find().sort("created_at", -1))
    return [serialize_doc(t) for t in tariffs]

@app.post("/api/tariffs")
async def create_tariff(data: TariffCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tariff_doc = {
        "name": data.name,
        "price": data.price,
        "currency": data.currency,
        "description": data.description,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = tariffs_collection.insert_one(tariff_doc)
    log_activity(current_user["id"], current_user["name"], "create", "tariff", str(result.inserted_id), {"name": data.name})
    tariff = tariffs_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(tariff)

@app.put("/api/tariffs/{tariff_id}")
async def update_tariff(tariff_id: str, data: TariffUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        tariffs_collection.update_one({"_id": ObjectId(tariff_id)}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "tariff", tariff_id, update_data)
    
    tariff = tariffs_collection.find_one({"_id": ObjectId(tariff_id)})
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return serialize_doc(tariff)

@app.delete("/api/tariffs/{tariff_id}")
async def delete_tariff(tariff_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if any clients use this tariff
    if clients_collection.count_documents({"tariff_id": tariff_id}) > 0:
        raise HTTPException(status_code=400, detail="Tariff is in use by clients")
    
    result = tariffs_collection.delete_one({"_id": ObjectId(tariff_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tariff not found")
    log_activity(current_user["id"], current_user["name"], "delete", "tariff", tariff_id, {})
    return {"message": "Tariff deleted"}

# ==================== GROUPS ENDPOINTS ====================

@app.get("/api/groups")
async def get_groups(current_user: dict = Depends(get_current_user)):
    groups = list(groups_collection.find().sort("name", 1))
    return [serialize_doc(g) for g in groups]

@app.post("/api/groups")
async def create_group(data: GroupCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check for duplicate name
    existing = groups_collection.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    
    group_doc = {
        "name": data.name,
        "color": data.color or "#6B7280",
        "description": data.description or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = groups_collection.insert_one(group_doc)
    log_activity(current_user["id"], current_user["name"], "create", "group", str(result.inserted_id), {"name": data.name})
    group = groups_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(group)

@app.put("/api/groups/{group_id}")
async def update_group(group_id: str, data: GroupUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        groups_collection.update_one({"_id": ObjectId(group_id)}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "group", group_id, update_data)
    
    group = groups_collection.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return serialize_doc(group)

@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if any clients use this group
    clients_in_group = clients_collection.count_documents({"group_id": group_id})
    if clients_in_group > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete group: {clients_in_group} clients are using it")
    
    result = groups_collection.delete_one({"_id": ObjectId(group_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    log_activity(current_user["id"], current_user["name"], "delete", "group", group_id, {})
    return {"message": "Group deleted"}

# ==================== SETTINGS ENDPOINTS ====================

@app.get("/api/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    settings = settings_collection.find_one({"key": "system"})
    if settings:
        return serialize_doc(settings)
    return {"currency": "USD"}

@app.put("/api/settings")
async def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        settings_collection.update_one(
            {"key": "system"},
            {"$set": update_data},
            upsert=True
        )
        log_activity(current_user["id"], current_user["name"], "update", "settings", "system", update_data)
    
    settings = settings_collection.find_one({"key": "system"})
    return serialize_doc(settings)

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
    query = {"is_archived": {"$ne": True} if not is_archived else True}
    
    # Exclude sold clients if requested (for main clients list)
    if exclude_sold and not status:
        query["status"] = {"$ne": "sold"}
    
    # Role-based filtering
    if current_user["role"] != "admin":
        query["manager_id"] = current_user["id"]
    
    # Search by phone or name
    if search:
        query["$or"] = [
            {"phone": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    # Filter by status (overrides exclude_sold)
    if status:
        query["status"] = status
    
    # Filter by group
    if group_id:
        query["group_id"] = group_id
    
    # Date filters
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        if date_query:
            query["created_at"] = date_query
    
    clients = list(clients_collection.find(query).sort("created_at", -1))
    result = []
    for c in clients:
        client = serialize_doc(c)
        # Add tariff info
        if client.get("tariff_id"):
            tariff = tariffs_collection.find_one({"_id": ObjectId(client["tariff_id"])})
            if tariff:
                client["tariff_name"] = tariff["name"]
                client["tariff_price"] = tariff["price"]
        # Add group info
        if client.get("group_id"):
            group = groups_collection.find_one({"_id": ObjectId(client["group_id"])})
            if group:
                client["group_name"] = group["name"]
                client["group_color"] = group["color"]
        # Add manager info
        if client.get("manager_id"):
            manager = users_collection.find_one({"_id": ObjectId(client["manager_id"])})
            if manager:
                client["manager_name"] = manager["name"]
        result.append(client)
    return result

@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = serialize_doc(client)
    # Add tariff info
    if result.get("tariff_id"):
        tariff = tariffs_collection.find_one({"_id": ObjectId(result["tariff_id"])})
        if tariff:
            result["tariff_name"] = tariff["name"]
            result["tariff_price"] = tariff["price"]
    return result

@app.post("/api/clients")
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    # Check for duplicate phone
    existing = clients_collection.find_one({"phone": data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already exists")
    
    client_doc = {
        "name": data.name,
        "phone": data.phone,
        "source": data.source,
        "manager_id": data.manager_id or current_user["id"],
        "status": data.status,
        "is_lead": data.is_lead,
        "is_archived": False,
        "tariff_id": data.tariff_id,
        "group_id": data.group_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = clients_collection.insert_one(client_doc)
    client_id = str(result.inserted_id)
    
    # Create initial comment if provided
    if data.initial_comment:
        notes_collection.insert_one({
            "client_id": client_id,
            "text": data.initial_comment,
            "author_id": current_user["id"],
            "author_name": current_user["name"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create reminder if provided
    if data.reminder_text and data.reminder_at:
        manager_id = data.manager_id or current_user["id"]
        reminders_collection.insert_one({
            "client_id": client_id,
            "user_id": manager_id,
            "text": data.reminder_text,
            "remind_at": data.reminder_at,
            "is_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    log_activity(current_user["id"], current_user["name"], "create", "client", client_id, {"name": data.name})
    client = clients_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(client)

@app.put("/api/clients/{client_id}")
async def update_client(client_id: str, data: ClientUpdate, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    old_status = client.get("status")
    
    if update_data:
        clients_collection.update_one({"_id": ObjectId(client_id)}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "client", client_id, 
                    {"fields": list(update_data.keys()), "old_status": old_status, "new_status": update_data.get("status")})
    
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    return serialize_doc(client)

@app.delete("/api/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    clients_collection.delete_one({"_id": ObjectId(client_id)})
    notes_collection.delete_many({"client_id": client_id})
    payments_collection.delete_many({"client_id": client_id})
    reminders_collection.delete_many({"client_id": client_id})
    log_activity(current_user["id"], current_user["name"], "delete", "client", client_id, {"name": client.get("name")})
    return {"message": "Client deleted"}

# Archive/Restore client
@app.post("/api/clients/{client_id}/archive")
async def archive_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    archived_at = datetime.now(timezone.utc).isoformat()
    clients_collection.update_one(
        {"_id": ObjectId(client_id)}, 
        {"$set": {"is_archived": True, "archived_at": archived_at}}
    )
    log_activity(current_user["id"], current_user["name"], "archive", "client", client_id, {"name": client.get("name")})
    return {"message": "Client archived"}

@app.post("/api/clients/{client_id}/restore")
async def restore_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    clients_collection.update_one(
        {"_id": ObjectId(client_id)}, 
        {"$set": {"is_archived": False}, "$unset": {"archived_at": ""}}
    )
    log_activity(current_user["id"], current_user["name"], "restore", "client", client_id, {"name": client.get("name")})
    return {"message": "Client restored"}

# Convert to lead
@app.post("/api/clients/{client_id}/convert-to-lead")
async def convert_to_lead(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    clients_collection.update_one(
        {"_id": ObjectId(client_id)}, 
        {"$set": {"is_lead": True, "status": "new"}}
    )
    log_activity(current_user["id"], current_user["name"], "convert_to_lead", "client", client_id, {"name": client.get("name")})
    return {"message": "Client converted to lead"}

# ==================== IMPORT ENDPOINTS ====================

@app.post("/api/import/preview")
async def import_preview(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Preview import data before saving"""
    content = await file.read()
    rows = []
    errors = []
    
    try:
        # Try CSV first
        content_str = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content_str))
        
        for i, row in enumerate(reader):
            try:
                # Normalize column names (case-insensitive)
                normalized = {}
                for k, v in row.items():
                    key = k.lower().strip() if k else ''
                    normalized[key] = v.strip() if v else ''
                
                # Map to our fields
                name = normalized.get('name', normalized.get('ism', ''))
                phone = normalized.get('phone', normalized.get('telefon', normalized.get('tel', '')))
                source = normalized.get('source', normalized.get('manba', ''))
                status = normalized.get('status', normalized.get('holat', 'new'))
                
                if not name or not phone:
                    errors.append({"row": i + 2, "error": "Name and phone are required"})
                    continue
                
                # Check for duplicate
                existing = clients_collection.find_one({"phone": phone})
                is_duplicate = existing is not None
                
                rows.append({
                    "row": i + 2,
                    "name": name,
                    "phone": phone,
                    "source": source,
                    "status": status if status in ['new', 'contacted', 'sold'] else 'new',
                    "is_duplicate": is_duplicate,
                    "valid": not is_duplicate
                })
            except Exception as e:
                errors.append({"row": i + 2, "error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    return {
        "total": len(rows) + len(errors),
        "valid": len([r for r in rows if r["valid"]]),
        "duplicates": len([r for r in rows if r["is_duplicate"]]),
        "errors": len(errors),
        "rows": rows,
        "error_rows": errors
    }

@app.post("/api/import/save")
async def import_save(
    rows: List[ImportRow],
    current_user: dict = Depends(get_current_user)
):
    """Save imported clients"""
    success = 0
    failed = []
    
    for i, row in enumerate(rows):
        try:
            # Skip duplicates
            existing = clients_collection.find_one({"phone": row.phone})
            if existing:
                failed.append({"row": i + 1, "phone": row.phone, "error": "Duplicate phone"})
                continue
            
            client_doc = {
                "name": row.name,
                "phone": row.phone,
                "source": row.source,
                "manager_id": row.manager_id or current_user["id"],
                "status": row.status,
                "is_lead": True,
                "is_archived": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            clients_collection.insert_one(client_doc)
            success += 1
        except Exception as e:
            failed.append({"row": i + 1, "phone": row.phone, "error": str(e)})
    
    log_activity(current_user["id"], current_user["name"], "import", "client", "", {"success": success, "failed": len(failed)})
    
    return {
        "success": success,
        "failed": len(failed),
        "failed_rows": failed
    }

# ==================== NOTES/COMMENTS ENDPOINTS ====================

@app.get("/api/notes/{client_id}")
async def get_notes(client_id: str, current_user: dict = Depends(get_current_user)):
    notes = list(notes_collection.find({"client_id": client_id}).sort("created_at", -1))
    return [serialize_doc(n) for n in notes]

@app.post("/api/notes")
async def create_note(data: NoteCreate, current_user: dict = Depends(get_current_user)):
    note_doc = {
        "client_id": data.client_id,
        "text": data.text,
        "author_id": current_user["id"],
        "author_name": current_user["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = notes_collection.insert_one(note_doc)
    log_activity(current_user["id"], current_user["name"], "create", "note", str(result.inserted_id), {"client_id": data.client_id})
    note = notes_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(note)

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    note = notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("author_id") != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    notes_collection.delete_one({"_id": ObjectId(note_id)})
    log_activity(current_user["id"], current_user["name"], "delete", "note", note_id, {})
    return {"message": "Note deleted"}

# ==================== PAYMENTS ENDPOINTS ====================

@app.get("/api/payments")
async def get_all_payments(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    
    payments = list(payments_collection.find(query).sort("date", -1))
    result = []
    for p in payments:
        payment = serialize_doc(p)
        client = clients_collection.find_one({"_id": ObjectId(payment["client_id"])})
        if client:
            # Role check
            if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
                continue
            payment["client_name"] = client["name"]
            payment["client_phone"] = client["phone"]
        result.append(payment)
    return result

@app.get("/api/payments/client/{client_id}")
async def get_client_payments(client_id: str, current_user: dict = Depends(get_current_user)):
    payments = list(payments_collection.find({"client_id": client_id}).sort("date", -1))
    return [serialize_doc(p) for p in payments]

@app.post("/api/payments")
async def create_payment(data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    # Use system currency if not specified
    currency = data.currency or get_system_currency()
    
    payment_doc = {
        "client_id": data.client_id,
        "amount": data.amount,
        "currency": currency,
        "status": data.status,
        "date": data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "comment": data.comment or "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = payments_collection.insert_one(payment_doc)
    log_activity(current_user["id"], current_user["name"], "create", "payment", str(result.inserted_id), 
                {"client_id": data.client_id, "amount": data.amount, "currency": currency})
    payment = payments_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(payment)

@app.put("/api/payments/{payment_id}")
async def update_payment(payment_id: str, data: PaymentUpdate, current_user: dict = Depends(get_current_user)):
    # Get the old payment for comparison
    old_payment = payments_collection.find_one({"_id": ObjectId(payment_id)})
    if not old_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Validate amount is not negative
    if data.amount is not None and data.amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        payments_collection.update_one({"_id": ObjectId(payment_id)}, {"$set": update_data})
        
        # Log activity with old and new values
        changes = {}
        for key, new_value in update_data.items():
            old_value = old_payment.get(key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}
        
        log_activity(current_user["id"], current_user["name"], "update", "payment", payment_id, 
                    {"changes": changes, "client_id": old_payment.get("client_id")})
    
    payment = payments_collection.find_one({"_id": ObjectId(payment_id)})
    return serialize_doc(payment)

@app.delete("/api/payments/{payment_id}")
async def delete_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    result = payments_collection.delete_one({"_id": ObjectId(payment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    log_activity(current_user["id"], current_user["name"], "delete", "payment", payment_id, {})
    return {"message": "Payment deleted"}

# ==================== REMINDERS ENDPOINTS ====================

@app.get("/api/reminders")
async def get_reminders(
    include_completed: bool = False,
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    if not include_completed:
        query["is_completed"] = {"$ne": True}
    
    reminders = list(reminders_collection.find(query).sort("remind_at", 1))
    result = []
    for r in reminders:
        reminder = serialize_doc(r)
        client = clients_collection.find_one({"_id": ObjectId(reminder["client_id"])})
        if client:
            reminder["client_name"] = client["name"]
        result.append(reminder)
    return result

@app.get("/api/reminders/overdue")
async def get_overdue_reminders(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    query = {
        "user_id": current_user["id"],
        "remind_at": {"$lt": now},
        "is_completed": {"$ne": True}
    }
    reminders = list(reminders_collection.find(query).sort("remind_at", 1))
    result = []
    for r in reminders:
        reminder = serialize_doc(r)
        client = clients_collection.find_one({"_id": ObjectId(reminder["client_id"])})
        if client:
            reminder["client_name"] = client["name"]
        result.append(reminder)
    return result

@app.post("/api/reminders")
async def create_reminder(data: ReminderCreate, current_user: dict = Depends(get_current_user)):
    reminder_doc = {
        "client_id": data.client_id,
        "user_id": current_user["id"],
        "text": data.text,
        "remind_at": data.remind_at,
        "is_completed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = reminders_collection.insert_one(reminder_doc)
    log_activity(current_user["id"], current_user["name"], "create", "reminder", str(result.inserted_id), {"client_id": data.client_id})
    reminder = reminders_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(reminder)

@app.put("/api/reminders/{reminder_id}")
async def update_reminder(reminder_id: str, data: ReminderUpdate, current_user: dict = Depends(get_current_user)):
    reminder = reminders_collection.find_one({"_id": ObjectId(reminder_id)})
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.get("user_id") != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        reminders_collection.update_one({"_id": ObjectId(reminder_id)}, {"$set": update_data})
    
    reminder = reminders_collection.find_one({"_id": ObjectId(reminder_id)})
    return serialize_doc(reminder)

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, current_user: dict = Depends(get_current_user)):
    reminder = reminders_collection.find_one({"_id": ObjectId(reminder_id)})
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.get("user_id") != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
    return {"message": "Reminder deleted"}

# ==================== NOTIFICATIONS ENDPOINTS ====================

@app.get("/api/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    if unread_only:
        query["is_read"] = False
    
    notifications = list(notifications_collection.find(query).sort("created_at", -1).limit(limit))
    return [serialize_doc(n) for n in notifications]

@app.get("/api/notifications/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    count = notifications_collection.count_documents({
        "user_id": current_user["id"],
        "is_read": False
    })
    return {"count": count}

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    notifications_collection.update_one(
        {"_id": ObjectId(notification_id), "user_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

@app.put("/api/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    notifications_collection.update_many(
        {"user_id": current_user["id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}

@app.get("/api/notifications/check-reminders")
async def check_reminders(current_user: dict = Depends(get_current_user)):
    """Check for due reminders and create notifications"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Find due reminders that haven't been notified
    due_reminders = list(reminders_collection.find({
        "user_id": current_user["id"],
        "remind_at": {"$lte": now},
        "is_completed": {"$ne": True},
        "notified": {"$ne": True}
    }))
    
    new_notifications = []
    for reminder in due_reminders:
        client = clients_collection.find_one({"_id": ObjectId(reminder["client_id"])})
        client_name = client["name"] if client else "Unknown"
        
        # Create notification
        notification = {
            "user_id": current_user["id"],
            "title": f"Reminder: {client_name}",
            "message": reminder["text"],
            "type": "reminder",
            "entity_id": str(reminder["_id"]),
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        result = notifications_collection.insert_one(notification)
        notification["id"] = str(result.inserted_id)
        new_notifications.append(notification)
        
        # Mark reminder as notified
        reminders_collection.update_one(
            {"_id": reminder["_id"]},
            {"$set": {"notified": True}}
        )
    
    return {"new_notifications": new_notifications}

# ==================== STATUSES ENDPOINTS ====================

@app.get("/api/statuses")
async def get_statuses(current_user: dict = Depends(get_current_user)):
    statuses = list(statuses_collection.find().sort("order", 1))
    return [serialize_doc(s) for s in statuses]

@app.post("/api/statuses")
async def create_status(data: StatusCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    status_doc = {
        "name": data.name,
        "color": data.color,
        "order": data.order,
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = statuses_collection.insert_one(status_doc)
    log_activity(current_user["id"], current_user["name"], "create", "status", str(result.inserted_id), {"name": data.name})
    status = statuses_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(status)

@app.put("/api/statuses/{status_id}")
async def update_status(status_id: str, data: StatusUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        statuses_collection.update_one({"_id": ObjectId(status_id)}, {"$set": update_data})
        log_activity(current_user["id"], current_user["name"], "update", "status", status_id, update_data)
    
    status = statuses_collection.find_one({"_id": ObjectId(status_id)})
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return serialize_doc(status)

@app.delete("/api/statuses/{status_id}")
async def delete_status(status_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    status = statuses_collection.find_one({"_id": ObjectId(status_id)})
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    
    if status.get("is_default"):
        raise HTTPException(status_code=400, detail="Cannot delete default status")
    
    # Check if any clients use this status
    if clients_collection.count_documents({"status": status["name"]}) > 0:
        raise HTTPException(status_code=400, detail="Status is in use by clients")
    
    statuses_collection.delete_one({"_id": ObjectId(status_id)})
    log_activity(current_user["id"], current_user["name"], "delete", "status", status_id, {"name": status["name"]})
    return {"message": "Status deleted"}

# ==================== ACTIVITY LOG ENDPOINTS ====================

@app.get("/api/activity-log")
async def get_activity_log(
    entity_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    activities = list(activity_log_collection.find(query).sort("created_at", -1).limit(limit))
    return [serialize_doc(a) for a in activities]

# ==================== AUDIO FILES ENDPOINTS ====================

@app.get("/api/audio/{client_id}")
async def get_client_audio_files(client_id: str, current_user: dict = Depends(get_current_user)):
    files = list(audio_files_collection.find({"client_id": client_id}).sort("created_at", -1))
    return [serialize_doc(f) for f in files]

@app.post("/api/audio/upload")
async def upload_audio(
    client_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3", "audio/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: mp3, wav, ogg, webm")
    
    # Generate unique filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{client_id}_{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Save metadata to database
    audio_doc = {
        "client_id": client_id,
        "filename": filename,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "uploader_id": current_user["id"],
        "uploader_name": current_user["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = audio_files_collection.insert_one(audio_doc)
    log_activity(current_user["id"], current_user["name"], "upload", "audio", str(result.inserted_id), {"client_id": client_id, "filename": file.filename})
    
    audio = audio_files_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(audio)

@app.get("/api/audio/file/{audio_id}")
async def get_audio_file(audio_id: str, token: Optional[str] = None, current_user: dict = None):
    """
    Serve audio file. Supports both:
    - Authorization header (for API calls)
    - Token query parameter (for HTML5 audio player)
    """
    # Try to authenticate via query parameter token if no current_user
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user = users_collection.find_one({"email": payload.get("sub")})
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    elif not current_user:
        # Try to get from Authorization header
        raise HTTPException(status_code=401, detail="Authentication required")
    
    audio = audio_files_collection.find_one({"_id": ObjectId(audio_id)})
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Get file size for Content-Length header
    file_size = os.path.getsize(filepath)
    
    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
    
    headers = {
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache"
    }
    
    return StreamingResponse(
        iterfile(), 
        media_type=audio["content_type"],
        headers=headers
    )

@app.get("/api/audio/stream/{audio_id}")
async def stream_audio_public(audio_id: str, token: str):
    """
    Public audio streaming endpoint with token authentication via query param.
    Used by HTML5 audio player which cannot send Authorization headers.
    """
    # Validate token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    audio = audio_files_collection.find_one({"_id": ObjectId(audio_id)})
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    file_size = os.path.getsize(filepath)
    
    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
    
    headers = {
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache"
    }
    
    return StreamingResponse(
        iterfile(), 
        media_type=audio["content_type"],
        headers=headers
    )

@app.delete("/api/audio/{audio_id}")
async def delete_audio(audio_id: str, current_user: dict = Depends(get_current_user)):
    audio = audio_files_collection.find_one({"_id": ObjectId(audio_id)})
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Delete file from disk
    filepath = os.path.join(UPLOAD_DIR, audio["filename"])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete from database
    audio_files_collection.delete_one({"_id": ObjectId(audio_id)})
    log_activity(current_user["id"], current_user["name"], "delete", "audio", audio_id, {"filename": audio["original_name"]})
    return {"message": "Audio deleted"}

# ==================== EXPORT ENDPOINTS ====================

@app.get("/api/export/clients")
async def export_clients(
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if current_user["role"] != "admin":
        query["manager_id"] = current_user["id"]
    
    clients = list(clients_collection.find(query).sort("created_at", -1))
    
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
                c.get("is_archived", False)
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clients_export.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Format not supported. Use: csv")

# ==================== DASHBOARD STATS ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    query = {"is_archived": {"$ne": True}}
    if current_user["role"] != "admin":
        query["manager_id"] = current_user["id"]
    
    # Today's date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Total clients
    total_clients = clients_collection.count_documents(query)
    
    # Today's leads
    today_query = {**query, "created_at": {"$regex": f"^{today}"}}
    todays_leads = clients_collection.count_documents(today_query)
    
    # Status counts
    new_count = clients_collection.count_documents({**query, "status": "new"})
    contacted_count = clients_collection.count_documents({**query, "status": "contacted"})
    sold_count = clients_collection.count_documents({**query, "status": "sold"})
    
    # Payment stats
    payment_query = {}
    if current_user["role"] != "admin":
        client_ids = [str(c["_id"]) for c in clients_collection.find(query, {"_id": 1})]
        payment_query = {"client_id": {"$in": client_ids}}
    
    total_paid = sum(p.get("amount", 0) for p in payments_collection.find({**payment_query, "status": "paid"}))
    total_pending = sum(p.get("amount", 0) for p in payments_collection.find({**payment_query, "status": "pending"}))
    
    # Overdue reminders count
    now = datetime.now(timezone.utc).isoformat()
    overdue_reminders = reminders_collection.count_documents({
        "user_id": current_user["id"],
        "remind_at": {"$lt": now},
        "is_completed": {"$ne": True}
    })
    
    # System currency
    currency = get_system_currency()
    
    return {
        "total_clients": total_clients,
        "todays_leads": todays_leads,
        "new_count": new_count,
        "contacted_count": contacted_count,
        "sold_count": sold_count,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "overdue_reminders": overdue_reminders,
        "currency": currency
    }

@app.get("/api/dashboard/recent-clients")
async def get_recent_clients(current_user: dict = Depends(get_current_user)):
    query = {"is_archived": {"$ne": True}}
    if current_user["role"] != "admin":
        query["manager_id"] = current_user["id"]
    
    clients = list(clients_collection.find(query).sort("created_at", -1).limit(5))
    return [serialize_doc(c) for c in clients]

@app.get("/api/dashboard/recent-notes")
async def get_recent_notes(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        notes = list(notes_collection.find().sort("created_at", -1).limit(5))
    else:
        client_ids = [str(c["_id"]) for c in clients_collection.find({"manager_id": current_user["id"]}, {"_id": 1})]
        notes = list(notes_collection.find({"client_id": {"$in": client_ids}}).sort("created_at", -1).limit(5))
    
    result = []
    for n in notes:
        note = serialize_doc(n)
        client = clients_collection.find_one({"_id": ObjectId(note["client_id"])})
        if client:
            note["client_name"] = client["name"]
        result.append(note)
    return result

@app.get("/api/dashboard/manager-stats")
async def get_manager_stats(current_user: dict = Depends(get_current_user)):
    """Get sales statistics per manager (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    managers = list(users_collection.find({}, {"password": 0}))
    result = []
    
    for manager in managers:
        manager_id = str(manager["_id"])
        
        # Get clients for this manager
        client_ids = [str(c["_id"]) for c in clients_collection.find({"manager_id": manager_id}, {"_id": 1})]
        
        # Count sold clients
        sold_count = clients_collection.count_documents({"manager_id": manager_id, "status": "sold"})
        
        # Total revenue
        total_revenue = sum(
            p.get("amount", 0) 
            for p in payments_collection.find({"client_id": {"$in": client_ids}, "status": "paid"})
        )
        
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
async def get_analytics(
    months: int = 6,
    current_user: dict = Depends(get_current_user)
):
    """Get monthly analytics data"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=months * 30)
    
    # Monthly sales data
    monthly_data = []
    current = start_date
    
    while current <= end_date:
        month_start = current.replace(day=1).strftime("%Y-%m")
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        # Count sold clients this month
        sold_query = {
            "status": "sold",
            "created_at": {"$regex": f"^{month_start}"}
        }
        sold_count = clients_collection.count_documents(sold_query)
        
        # Revenue this month
        revenue = sum(
            p.get("amount", 0)
            for p in payments_collection.find({
                "status": "paid",
                "date": {"$regex": f"^{month_start}"}
            })
        )
        
        # New leads this month
        new_leads = clients_collection.count_documents({
            "created_at": {"$regex": f"^{month_start}"}
        })
        
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
    tariffs = list(tariffs_collection.find())
    for tariff in tariffs:
        tariff_id = str(tariff["_id"])
        count = clients_collection.count_documents({"tariff_id": tariff_id, "status": "sold"})
        tariff_stats.append({
            "name": tariff["name"],
            "price": tariff["price"],
            "sold_count": count,
            "revenue": count * tariff["price"]
        })
    
    # Calculate month-over-month changes
    if len(monthly_data) >= 2:
        current_month = monthly_data[-1]
        prev_month = monthly_data[-2]
        
        revenue_change = current_month["revenue"] - prev_month["revenue"]
        revenue_change_pct = ((current_month["revenue"] - prev_month["revenue"]) / prev_month["revenue"] * 100) if prev_month["revenue"] > 0 else 0
        
        deals_change = current_month["sold_count"] - prev_month["sold_count"]
        deals_change_pct = ((current_month["sold_count"] - prev_month["sold_count"]) / prev_month["sold_count"] * 100) if prev_month["sold_count"] > 0 else 0
    else:
        revenue_change = 0
        revenue_change_pct = 0
        deals_change = 0
        deals_change_pct = 0
    
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
