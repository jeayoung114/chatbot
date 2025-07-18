from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import importlib
import os
from supabase import create_client, Client
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Auth settings
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MODEL_MAP = {
    "openai": "models.openai_model",
    "huggingface": "models.huggingface_model",
    "custom": "models.custom_model",
    "claude": "models.claude_model"
}

class UserRegister(BaseModel):
    email: str
    password: str
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdateKeys(BaseModel):
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# Password hashing helpers
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# JWT helpers
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise credentials_exception
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = supabase.table("users").select("*").eq("id", user_id).single().execute().data
    if not user:
        raise credentials_exception
    return user

@app.post("/register")
async def register(user: UserRegister):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    # Check if user exists
    exists = supabase.table("users").select("id").eq("email", user.email).execute().data
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    hashed = hash_password(user.password)
    supabase.table("users").insert({
        "id": user_id,
        "email": user.email,
        "password_hash": hashed,
        "openai_api_key": user.openai_api_key,
        "claude_api_key": user.claude_api_key
    }).execute()
    return {"msg": "User registered"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    db_user = supabase.table("users").select("*").eq("email", user.email).single().execute().data
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "openai_api_key": current_user.get("openai_api_key"), "claude_api_key": current_user.get("claude_api_key")}

@app.post("/update_keys")
async def update_keys(keys: UserUpdateKeys, current_user: dict = Depends(get_current_user)):
    updates = {}
    if keys.openai_api_key is not None:
        updates["openai_api_key"] = keys.openai_api_key
    if keys.claude_api_key is not None:
        updates["claude_api_key"] = keys.claude_api_key
    if updates:
        supabase.table("users").update(updates).eq("id", current_user["id"]).execute()
    return {"msg": "API keys updated"}

class ChatCreate(BaseModel):
    title: Optional[str] = None

class MessageCreate(BaseModel):
    chat_id: str
    role: str
    content: str

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html") as f:
        return f.read()

@app.get("/chats")
async def list_chats():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    data = supabase.table("chats").select("*").order("created_at", desc=True).execute()
    return data.data

@app.post("/chats")
async def create_chat(chat: ChatCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    chat_id = str(uuid.uuid4())
    title = chat.title or "New Chat"
    data = supabase.table("chats").insert({"id": chat_id, "title": title}).execute()
    return {"id": chat_id, "title": title}

@app.get("/chats/{chat_id}/messages")
async def list_messages(chat_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    data = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at").execute()
    return data.data

@app.post("/chats/{chat_id}/messages")
async def add_message(chat_id: str, msg: MessageCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    data = supabase.table("messages").insert({
        "chat_id": chat_id,
        "role": msg.role,
        "content": msg.content
    }).execute()
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    prompt = data.get("prompt")
    model_name = data.get("model", "openai")
    chat_id = data.get("chat_id")
    model_module = importlib.import_module(MODEL_MAP[model_name])
    if model_name == "claude":
        api_key = current_user.get("claude_api_key")
        response = model_module.generate_response(prompt, api_key=api_key)
    elif model_name == "openai":
        api_key = current_user.get("openai_api_key")
        response = model_module.generate_response(prompt, api_key=api_key)
    else:
        response = model_module.generate_response(prompt)
    # Save user and bot messages if chat_id is provided
    if supabase and chat_id:
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "user",
            "content": prompt
        }).execute()
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "bot",
            "content": response
        }).execute()
        # Update chat title using OpenAI for the first 5 rounds (10 messages)
        messages = supabase.table("messages").select("*").eq("chat_id", chat_id).order("created_at").execute().data
        if messages and len(messages) <= 10:
            # Use the last 5 user+bot pairs for context
            convo = []
            for m in messages[-10:]:
                convo.append(f"{m['role'].capitalize()}: {m['content']}")
            title_prompt = (
                "Generate a short, descriptive title for this conversation:\n" +
                "\n".join(convo) +
                "\nTitle:"
            )
            title_model = MODEL_MAP["openai"]
            title_module = importlib.import_module(title_model)
            title_api_key = current_user.get("openai_api_key")
            title = title_module.generate_response(title_prompt, api_key=title_api_key).strip().replace('\n', ' ')
            if len(title) > 60:
                title = title[:57] + "..."
            supabase.table("chats").update({"title": title}).eq("id", chat_id).execute()
    return JSONResponse({"response": response}) 