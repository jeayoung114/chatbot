# Multi-Model Chatbot App

A modern, ChatGPT-style chatbot web app with support for multiple models (OpenAI, Claude, Hugging Face, custom), user authentication, per-user API keys, and Supabase-backed chat history.

---

## Features
- ChatGPT-like UI with sidebar chat history
- Supports OpenAI, Claude, Hugging Face, and custom models
- User registration, login, and JWT authentication
- Per-user API key management (OpenAI, Claude)
- Supabase as the backend database for users, chats, and messages
- Automatic chat title generation using OpenAI (updates for first 5 rounds)
- Error handling and robust frontend/backend integration

---

## Setup

### 1. Clone the Repository
```sh
git clone <https://github.com/jeayoung114/chatbot_vibecoding.git>
cd chatbot
```

### 2. Python Environment
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Supabase Setup
- Create a Supabase project at https://app.supabase.com/
- In the SQL editor, run:
```sql
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  openai_api_key text,
  claude_api_key text,
  created_at timestamp with time zone default timezone('utc', now())
);

create table if not exists chats (
  id uuid primary key default gen_random_uuid(),
  title text,
  created_at timestamp with time zone default timezone('utc', now())
);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid references chats(id) on delete cascade,
  role text,
  content text,
  created_at timestamp with time zone default timezone('utc', now())
);

create index if not exists idx_messages_chat_id on messages(chat_id);
```
- Get your `SUPABASE_URL` and `SUPABASE_KEY` from the project settings.

### 5. Environment Variables
Add to your `~/.zshrc` or export in your shell:
```sh
export SUPABASE_URL=your_supabase_url
export SUPABASE_KEY=your_supabase_key
export SECRET_KEY=your_secret_key
```

### 6. Start the Server
```sh
uvicorn app:app --reload
```

---

## Usage
- Open [http://localhost:8000](http://localhost:8000) in your browser.
- Register a new user (email, password, and your API keys for OpenAI/Claude).
- Start chatting! The sidebar will show your chat history with auto-generated titles.
- You can update your API keys in the user settings modal.

---

## Model Integration
- **OpenAI:** Uses per-user API key for GPT-3.5/4 via the OpenAI Python SDK.
- **Claude:** Uses per-user API key for Anthropic Claude via HTTP API.
- **Hugging Face:** Placeholder for Hugging Face Inference API (add your endpoint/token in `models/huggingface_model.py`).
- **Custom:** Simple echo or your own logic in `models/custom_model.py`.

---

## File Structure
```
chatbot/
├── app.py                # FastAPI backend
├── models/
│   ├── openai_model.py
│   ├── claude_model.py
│   ├── huggingface_model.py
│   └── custom_model.py
├── requirements.txt
├── static/
│   └── index.html        # Frontend (ChatGPT-style UI)
└── README.md
```

---

## Security Notes
- Passwords are hashed with bcrypt (passlib).
- JWT is used for authentication.
- API keys are stored per user in Supabase (consider encrypting in production).
- Always use HTTPS in production.

---

## Customization
- You can add more models by creating new wrappers in `models/` and updating `MODEL_MAP` in `app.py`.
- Adjust chat title generation logic in `app.py` as needed.
- Frontend is a single-page app in `static/index.html` (customize UI/UX as desired).

---

## License
MIT (or your preferred license) 