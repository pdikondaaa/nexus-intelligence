"""
===========================================================================
  Nexus intelligence — FastAPI Backend (Thin Pipeline Router)
===========================================================================

  This file is intentionally thin. All business logic lives in the layers/
  package. The pipeline flows exactly as:

  User Request
    ↓
  1.  Auth Layer               (layers/auth.py)        — Verify token, extract identity
    ↓
  2.  Guardrail (Security)     (layers/guardrail.py)   — Block unsafe actions, allow read-only
    ↓
  3.  AI Agent (Orchestrator)  (layers/agent.py)       — Understand intent, decide data source
    ↓
  4.  Secure Retrieval (Data)  (layers/retrieval.py)   — Fetch data based on user access
    ↓
  5.  PII Masking (Privacy)    (layers/pii_masking.py) — Remove sensitive info (salary, email, etc.)
    ↓
  6.  LLM (Response Gen)       (layers/llm_response.py)— Generate answer from safe/filtered data
    ↓
  User Response

===========================================================================
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List

# ─── Import each architectural layer ──────────────────────────
from layers.auth import authenticate_request, AuthResult
from layers.guardrail import validate_messages, Message as GuardrailMessage
from layers.agent import analyze_intent
from layers.retrieval import fetch_data
from layers.pii_masking import mask_pii_in_context
from layers.llm_response import stream_llm_response


app = FastAPI(title="Nexus intelligence — Layered Architecture")

# Allow the React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


# ─── Health Check ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "architecture": "layered-pipeline"}


# ─── Main Chat Pipeline ──────────────────────────────────────

@app.post("/api/chat")
async def chat_pipeline(request: Request, chat_request: ChatRequest):
    """
    Orchestrates the full layered pipeline for every chat request.
    Each step is clearly separated into its own module.
    """

    print("\n" + "=" * 60)
    print("  📩 NEW REQUEST — Starting Pipeline")
    print("=" * 60)

    # ══════════════════════════════════════════════════════════
    # LAYER 1: AUTH — Verify token, extract identity
    # ══════════════════════════════════════════════════════════
    try:
        auth: AuthResult = authenticate_request(request)
    except Exception as auth_err:
        # Allow unauthenticated users to still chat (without data retrieval)
        print(f"⚠️  Auth: No valid token — proceeding without data access ({auth_err})")
        auth = AuthResult(access_token="", user_name="Anonymous", user_email=None)

    # ══════════════════════════════════════════════════════════
    # LAYER 2: GUARDRAIL — Block unsafe actions, allow read-only
    # ══════════════════════════════════════════════════════════
    guardrail_messages = [
        GuardrailMessage(role=m.role, content=m.content)
        for m in chat_request.messages
    ]
    guardrail_result = validate_messages(guardrail_messages)

    if not guardrail_result.passed:
        print(f"🚫 Guardrail BLOCKED ({guardrail_result.action_type}): {guardrail_result.reason}")
        return JSONResponse(
            status_code=400,
            content={"error": guardrail_result.reason},
        )

    # ══════════════════════════════════════════════════════════
    # LAYER 3: AI AGENT — Understand intent, decide data source
    # ══════════════════════════════════════════════════════════
    latest_query = chat_request.messages[-1].content
    decision = analyze_intent(latest_query)

    print(f"📋 Agent Decision: intent={decision.intent}, source={decision.data_source}, "
          f"skip_retrieval={decision.skip_retrieval}")

    # ══════════════════════════════════════════════════════════
    # LAYER 4: SECURE RETRIEVAL — Fetch data based on user access
    # ══════════════════════════════════════════════════════════
    if decision.skip_retrieval:
        raw_context = ""
        print("⏭️  Retrieval: Skipped (agent decision)")
    elif auth.access_token:
        raw_context = fetch_data(
            query=decision.optimized_query,
            data_source=decision.data_source,
            auth=auth,
        )
    else:
        raw_context = "[No data context — user is not authenticated.]"

    # ══════════════════════════════════════════════════════════
    # LAYER 5: PII MASKING — Remove sensitive info before LLM
    # ══════════════════════════════════════════════════════════
    masked_context = mask_pii_in_context(raw_context) if raw_context else ""
    if raw_context:
        print("🛡️  PII Masking: Context sanitised (salary, email, phone, etc. redacted)")

    # ══════════════════════════════════════════════════════════
    # LAYER 6: LLM — Generate answer from safe/filtered data
    # ══════════════════════════════════════════════════════════
    formatted_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_request.messages
    ]

    print("🚀 Pipeline: Handing off to LLM (using only safe, filtered data)...\n")

    return StreamingResponse(
        stream_llm_response(formatted_messages, masked_context),
        media_type="text/plain",
    )


# ─── Entrypoint ───────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
