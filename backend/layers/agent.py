"""
=====================  LAYER 3 — AI AGENT (Orchestrator)  =====================
Understands user intent and decides which data source or action to use.
Routes the query to the appropriate retrieval strategy based on what
the user is actually asking for.

Flow position: Security Guardrail → [AI Agent] → Secure Retrieval
=================================================================================
"""

import ollama
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# ─── Model Configuration ──────────────────────────────────────
AGENT_MODEL = "gpt-oss:120b-cloud"

# Load skill prompt from external file (if exists)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str, fallback: str) -> str:
    """Load a prompt from the prompts/ directory, fallback to inline."""
    prompt_file = _PROMPTS_DIR / filename
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8").strip()
    return fallback


# ─── Intent Classification ────────────────────────────────────

@dataclass
class AgentDecision:
    """
    The AI Agent's routing decision after analyzing user intent.

    Attributes:
        intent:           What the user wants (e.g., "search_documents", "greeting", "general_question")
        data_source:      Which source to query ("sharepoint", "none", or future sources)
        optimized_query:  Cleaned keywords for the data source search
        skip_retrieval:   If True, skip data retrieval entirely (greetings, meta-questions)
        reasoning:        Agent's internal reasoning for logging
    """
    intent: str
    data_source: str
    optimized_query: str
    skip_retrieval: bool = False
    reasoning: str = ""


# ─── Intent Detection (rule-based fast path) ──────────────────

# Patterns that don't need SharePoint retrieval at all
GREETING_PATTERNS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "hi there", "hello there", "thanks", "thank you", "bye",
    "goodbye", "see you", "ok", "okay",
]

META_QUESTION_PATTERNS = [
    "who are you", "what can you do", "what are you", "how do you work",
    "help me", "what is your name", "your capabilities",
]


def _is_greeting(text: str) -> bool:
    """Check if the message is a simple greeting that needs no data lookup."""
    clean = text.strip().lower().rstrip("!?.;,")
    return clean in GREETING_PATTERNS


def _is_meta_question(text: str) -> bool:
    """Check if the user is asking about the bot itself."""
    lower = text.lower()
    return any(pattern in lower for pattern in META_QUESTION_PATTERNS)


# ─── Keyword Extraction Prompt ────────────────────────────────

_DEFAULT_EXTRACTION_PROMPT = (
    "You are an extreme keyword extractor for a strict enterprise SharePoint Search Engine. "
    "Reduce the user's sentence down to ONLY the 1 to 3 most critical root NOUNS. "
    "You MUST permanently drop any dates, years (like 2026), verbs, numbers, or pleasantries. "
    "ONLY output the raw root nouns, nothing else.\n\n"
    "EXAMPLES:\n"
    "User: 'Can you please help me with the leave policy of 2026?' -> Output: leave policy\n"
    "User: 'I need to find the ppt template for presentations' -> Output: ppt template\n"
    "User: 'What are the upcoming official holidays?' -> Output: holiday\n"
    "User: 'Show me the color palate guidelines' -> Output: color palate\n"
    "User: 'How do I send recognition or appreciation to our team?' -> Output: recognition appreciation\n"
    "User: 'What is the total employee count out of interest?' -> Output: employee count\n"
    "User: 'Do we have birthday celebrations?' -> Output: birthday"
)


def _extract_keywords(user_message: str) -> str:
    """
    Use a lightweight LLM call to convert natural-language into
    optimized search keywords.
    """
    extraction_prompt = _load_prompt("skill_prompt.txt", _DEFAULT_EXTRACTION_PROMPT)

    try:
        response = ollama.chat(
            model=AGENT_MODEL,
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=False,
        )

        optimized = response["message"]["content"].strip()
        optimized = optimized.replace('"', "").replace("'", "")
        return optimized

    except Exception as e:
        print(f"⚠️  AI Agent: Keyword extraction failed — {e}")
        return user_message


# ─── Main Orchestrator Function ───────────────────────────────

def analyze_intent(user_message: str) -> AgentDecision:
    """
    The AI Agent's core function. Understands intent and decides:
      1. WHAT the user wants (intent classification)
      2. WHERE to get the data (data source selection)
      3. HOW to search for it (query optimisation)

    This is the single entry point called by the pipeline router (main.py).

    Returns an AgentDecision with routing instructions for downstream layers.
    """

    print("🧠 AI Agent: Analyzing user intent...")

    # ── Fast path: Greetings (no LLM needed, no retrieval needed) ──
    if _is_greeting(user_message):
        print("🎯 AI Agent Decision: GREETING → skip retrieval")
        return AgentDecision(
            intent="greeting",
            data_source="none",
            optimized_query="",
            skip_retrieval=True,
            reasoning="Simple greeting detected — no data lookup needed",
        )

    # ── Fast path: Meta-questions about the bot itself ──
    if _is_meta_question(user_message):
        print("🎯 AI Agent Decision: META_QUESTION → skip retrieval")
        return AgentDecision(
            intent="meta_question",
            data_source="none",
            optimized_query="",
            skip_retrieval=True,
            reasoning="User is asking about the bot — answer from system knowledge",
        )

    # ── Standard path: Enterprise data query → SharePoint ──
    print("🔄 AI Agent: Routing to SharePoint data source...")
    optimized_query = _extract_keywords(user_message)
    print(f"🎯 AI Agent Decision: SEARCH_DOCUMENTS → SharePoint → query='{optimized_query}'")

    return AgentDecision(
        intent="search_documents",
        data_source="sharepoint",
        optimized_query=optimized_query,
        skip_retrieval=False,
        reasoning=f"Enterprise data query — searching SharePoint with keywords: {optimized_query}",
    )
