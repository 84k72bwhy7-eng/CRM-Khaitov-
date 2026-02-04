from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId
import os

# App initialization
app = FastAPI(title="CourseCRM API", version="1.0.0")

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

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
clients_collection = db["clients"]
notes_collection = db["notes"]
payments_collection = db["payments"]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Pydantic Models
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

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[str] = None

class NoteCreate(BaseModel):
    client_id: str
    text: str

class PaymentCreate(BaseModel):
    client_id: str
    amount: float
    status: str = "pending"
    date: Optional[str] = None

class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[str] = None
    date: Optional[str] = None

# Helper functions
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

# Seed admin user
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

seed_admin()

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": "CourseCRM"}

# Auth endpoints
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
    user = users_collection.find_one({"_id": ObjectId(current_user["id"])}, {"password": 0})
    return serialize_doc(user)

# Users endpoints (admin only)
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
    return {"message": "User deleted"}

# Clients endpoints
@app.get("/api/clients")
async def get_clients(
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    
    # Role-based filtering
    if current_user["role"] != "admin":
        query["manager_id"] = current_user["id"]
    
    # Search by phone or name
    if search:
        query["$or"] = [
            {"phone": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    # Filter by status
    if status:
        query["status"] = status
    
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
    return [serialize_doc(c) for c in clients]

@app.get("/api/clients/{client_id}")
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    client = clients_collection.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access
    if current_user["role"] != "admin" and client.get("manager_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return serialize_doc(client)

@app.post("/api/clients")
async def create_client(data: ClientCreate, current_user: dict = Depends(get_current_user)):
    client_doc = {
        "name": data.name,
        "phone": data.phone,
        "source": data.source,
        "manager_id": data.manager_id or current_user["id"],
        "status": data.status,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = clients_collection.insert_one(client_doc)
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
    if update_data:
        clients_collection.update_one({"_id": ObjectId(client_id)}, {"$set": update_data})
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
    return {"message": "Client deleted"}

# Notes endpoints
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
    return {"message": "Note deleted"}

# Payments endpoints
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
    payment_doc = {
        "client_id": data.client_id,
        "amount": data.amount,
        "status": data.status,
        "date": data.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = payments_collection.insert_one(payment_doc)
    payment = payments_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(payment)

@app.put("/api/payments/{payment_id}")
async def update_payment(payment_id: str, data: PaymentUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        payments_collection.update_one({"_id": ObjectId(payment_id)}, {"$set": update_data})
    payment = payments_collection.find_one({"_id": ObjectId(payment_id)})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return serialize_doc(payment)

@app.delete("/api/payments/{payment_id}")
async def delete_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    result = payments_collection.delete_one({"_id": ObjectId(payment_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted"}

# Dashboard stats
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    query = {}
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
    
    total_paid = sum(p["amount"] for p in payments_collection.find({**payment_query, "status": "paid"}))
    total_pending = sum(p["amount"] for p in payments_collection.find({**payment_query, "status": "pending"}))
    
    return {
        "total_clients": total_clients,
        "todays_leads": todays_leads,
        "new_count": new_count,
        "contacted_count": contacted_count,
        "sold_count": sold_count,
        "total_paid": total_paid,
        "total_pending": total_pending
    }

@app.get("/api/dashboard/recent-clients")
async def get_recent_clients(current_user: dict = Depends(get_current_user)):
    query = {}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
