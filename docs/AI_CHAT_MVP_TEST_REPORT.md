# DavidAI AI Chat MVP — Test Report

**Date:** 5 June 2026  
**Database:** `davidai_dev`  
**Default model:** `qwen2.5:7b`  
**App URL:** http://127.0.0.1:5001

---

## Features delivered

| # | Requirement | Status |
|---|-------------|--------|
| 1 | AI Chat page `/chat` | Done |
| 2 | Ollama default model `qwen2.5:7b` | Done |
| 3 | Web search toggle (mock) | Done |
| 4 | PostgreSQL `conversations` + `messages` | Done |
| 5 | Chats linked to logged-in users | Done |
| 6 | API routes (`/api/chat`, `/api/conversations`, clear) | Done |
| 7 | Flask-Login — users see own chats only | Done |
| 8 | Dark theme matching DavidAI dashboard | Done |
| 9 | Error handling (Ollama, timeout, model, search) | Done |
| 10 | Migration `002_chat_tables` | Done |

---

## Files created/updated

| File | Purpose |
|------|---------|
| `backend/chat_service.py` | Ollama + mock web search |
| `backend/chat_routes.py` | Conversation storage helpers |
| `backend/app.py` | Chat API routes |
| `database/models.py` | `Conversation`, `Message` models |
| `database/migrations/versions/002_chat_tables.py` | DB migration |
| `frontend/templates/chat.html` | Chat UI |
| `frontend/static/css/chat.css` | Dark theme chat styles |
| `frontend/static/js/chat.js` | Chat frontend logic |
| `backend/test_chat_mvp.py` | Automated test script |
| `README.md` | Updated documentation |

---

## Automated test results — PASS (7/7)

```
[PASS] Register user
[PASS] GET /chat
[PASS] POST /api/chat hello — Qwen responded in 49.6s
[PASS] Messages saved in davidai_dev — conversation_id=1, messages=2
[PASS] Logout
[PASS] Login again
[PASS] History after re-login — messages=2
```

---

## API routes

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| GET | `/chat` | Required | Chat page |
| POST | `/api/chat` | Required | Send message, get response, save to DB |
| GET | `/api/conversations` | Required | Load user's chat history |
| POST | `/api/conversations/clear` | Required | Clear user's chat history |

---

## Timeout settings

| Setting | Value |
|---------|-------|
| Backend Ollama timeout | 180 seconds |
| Frontend AbortController | 195 seconds |

---

## Web search mode

- **Off:** Normal local Qwen via `/api/generate`
- **On:** Mock `search_web()` injects context (UK PM → Keir Starmer)
- No paid API keys configured

---

## Error codes

| Code | Message |
|------|---------|
| `ollama_offline` | Ollama is not running |
| `model_missing` | Model not installed — `ollama pull qwen2.5:7b` |
| `timeout` | Request timed out |
| `search_unavailable` | Web search failed |

---

## Manual browser test

1. Start Ollama and DavidAI app
2. Register/login at http://127.0.0.1:5001
3. Open `/chat`
4. Send `hello` — receive Qwen response
5. Logout and login — history persists
6. Optional: enable **Use web search**, ask *Who is the UK Prime Minister?*

---

## Security

- `.env` not exposed in code or documentation
- Chat history scoped to `current_user.id` via Flask-Login
- No API keys committed
