# FAAAHAA Intelligence — Architecture Walkthrough

## Layered Pipeline Architecture

```
User
 ↓
Chat UI          (src/components/ChatUI.jsx)
 ↓
Auth Layer       (src/authConfig.js + backend/layers/auth.py)
 ↓
Security Guardrail  (backend/layers/guardrail.py)
 ↓
AI Agent         (backend/layers/agent.py)
 ↓
Data Retrieval   (backend/layers/retrieval.py)  — Permission-Based via user's own token
 ↓
PII Masking      (backend/layers/pii_masking.py)
 ↓
LLM Response     (backend/layers/llm_response.py)
 ↓
User
```

---

## 1. Frontend Entry (`src/main.jsx`)

Initialises the MSAL (Microsoft Authentication) provider and renders the `<App />` component inside it. This is unchanged from before.

## 2. App Shell (`src/App.jsx`) — Thin Orchestrator

The App component is intentionally minimal. It manages:
- **Global chat state** (conversation list, active chat ID, session persistence)
- **Auth integration** (login/logout handlers, silent token acquisition)
- **Component composition** — renders `<Sidebar />` and `<ChatUI />`

## 3. Chat UI (`src/components/ChatUI.jsx`)

The main chat interface. When the user sends a message:
1. The user's message is immediately rendered on screen (zero-latency UX)
2. A Microsoft access token is acquired from MSAL
3. The full conversation history + token are sent to the backend via `src/services/api.js`
4. The streaming response is read chunk-by-chunk and painted to screen in real-time

## 4. API Service (`src/services/api.js`)

Centralises all HTTP communication. Handles:
- Bearer token injection into request headers
- Guardrail rejection errors (HTTP 400) surfaced as user-friendly messages
- Returns a `ReadableStreamDefaultReader` for streaming

---

## 5. Backend Router (`backend/main.py`) — Thin Pipeline Orchestrator

The FastAPI entry point is now a thin router that calls each layer in sequence:

```python
# Layer 1 — Auth
auth = authenticate_request(request)

# Layer 2 — Security Guardrail
guardrail_result = validate_messages(messages)

# Layer 3 — AI Agent (keyword extraction)
optimized_query = extract_search_query(latest_query)

# Layer 4 — Data Retrieval (permission-based)
context = search_sharepoint(optimized_query, auth)

# Layer 5 — PII Masking (on context)
masked_context = mask_pii_in_context(context)

# Layer 6 — LLM Response (streaming + output PII masking)
return StreamingResponse(stream_llm_response(messages, masked_context))
```

## 6. Auth Layer (`backend/layers/auth.py`)

Validates the bearer token from the request header. Extracts:
- User name, email, tenant ID from JWT claims
- Access token for permission-based SharePoint retrieval

Falls back gracefully if no token is present (chat still works, just without SharePoint data).

## 7. Security Guardrail (`backend/layers/guardrail.py`)

Inspects user messages **before** they reach the AI. Blocks:
- Prompt injection attacks (e.g., "ignore previous instructions")
- Blocked terms (configurable)
- Excessively long messages or conversation histories

If blocked, returns HTTP 400 with a user-friendly error message.

## 8. AI Agent (`backend/layers/agent.py`)

Uses a lightweight LLM call to convert natural language into optimised SharePoint search keywords. The extraction prompt is loaded from `backend/prompts/skill_prompt.txt` for easy editing.

## 9. Data Retrieval (`backend/layers/retrieval.py`)

Searches SharePoint Online using the **user's own access token**, guaranteeing permission-scoped results. Users only see documents they actually have access to.

## 10. PII Masking (`backend/layers/pii_masking.py`)

Applied in two places:
1. **On context** — Before injecting SharePoint results into the LLM prompt
2. **On output** — Before each streamed chunk reaches the user's browser

Detects and masks: emails, phone numbers, Aadhaar, PAN, credit cards, SSNs, IP addresses.

## 11. LLM Response (`backend/layers/llm_response.py`)

Constructs the system prompt (loaded from `backend/prompts/train_prompt.txt`), streams the Ollama response, and applies PII masking on every outgoing chunk.

---

## Prompt Files

| File | Purpose |
|------|---------|
| `backend/prompts/skill_prompt.txt` | AI Agent's keyword extraction instructions |
| `backend/prompts/train_prompt.txt` | Main LLM system prompt / persona definition |

These files can be edited without touching any code.
