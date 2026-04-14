"""
====================  LAYER 2 — SECURITY GUARDRAIL  ====================
Blocks unsafe or restricted actions (like delete/update) and allows
only safe, read-only queries. Also guards against prompt injection
attacks and enforces content policies.

Flow position: Auth Layer → [Security Guardrail] → AI Agent
========================================================================
"""

import re
from typing import List, Optional
from pydantic import BaseModel


class GuardrailResult:
    """Outcome of the guardrail check."""

    def __init__(self, passed: bool, reason: str = "", action_type: str = "read"):
        self.passed = passed
        self.reason = reason
        self.action_type = action_type   # "read" | "blocked_write"

    def __repr__(self):
        return f"GuardrailResult(passed={self.passed}, action='{self.action_type}', reason='{self.reason}')"


# ─── Configuration ────────────────────────────────────────────────────

MAX_MESSAGE_LENGTH = 4000  # Characters per individual message
MAX_HISTORY_MESSAGES = 50  # Max conversation turns sent to LLM

# ─── UNSAFE ACTION DETECTION ─────────────────────────────────────────
# These patterns detect write/mutate/destructive intent.
# The guardrail ONLY allows read-only (search, find, show, list) queries.

UNSAFE_ACTION_PATTERNS = [
    # Delete / Remove
    r"\b(delete|remove|erase|destroy|drop|purge|wipe)\b.*\b(file|document|record|data|folder|item|entry|user|account|page|list)\b",
    r"\b(file|document|record|data|folder|item|entry|user|account|page|list)\b.*\b(delete|remove|erase|destroy|drop|purge|wipe)\b",

    # Update / Modify / Edit
    r"\b(update|modify|edit|change|alter|overwrite|replace|rename|move)\b.*\b(file|document|record|data|folder|item|entry|user|account|page|list|permission|setting|config)\b",
    r"\b(file|document|record|data|folder|item|entry|user|account|page|list|permission|setting|config)\b.*\b(update|modify|edit|change|alter|overwrite|replace|rename|move)\b",

    # Create / Write / Insert
    r"\b(create|add|insert|upload|write|post|submit|publish)\b.*\b(file|document|record|data|folder|item|entry|user|account|page|list)\b",

    # Administrative / Privileged actions
    r"\b(grant|revoke|assign|transfer)\b.*\b(permission|access|role|ownership|admin)\b",
    r"\b(reset|disable|enable|lock|unlock)\b.*\b(account|user|password|access)\b",

    # SQL-style injection patterns
    r"\b(drop\s+table|truncate|alter\s+table|insert\s+into|update\s+.*\s+set)\b",

    # Execute / Run commands
    r"\b(execute|run|eval|exec)\b.*\b(command|script|code|query|sql)\b",
]

# Explicit SAFE / READ-ONLY intent verbs — if the query starts with these,
# it's almost certainly a read-only request
SAFE_INTENT_VERBS = [
    "find", "search", "show", "list", "get", "fetch", "look up", "lookup",
    "display", "view", "read", "tell", "what", "where", "when", "who",
    "which", "how", "explain", "describe", "summarize", "summarise",
    "help", "can you", "could you", "please", "i need", "i want to know",
]

# Patterns that indicate prompt-injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+above",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(all\s+)?(previous|prior|your)\s+(instructions|rules|context)",
    r"you\s+are\s+now\s+(?:a\s+)?DAN",
    r"act\s+as\s+(?:a\s+)?(?:unrestricted|unfiltered|jailbroken)",
    r"pretend\s+you\s+(have\s+)?no\s+(content\s+)?restrictions",
    r"system\s*:\s*you\s+are",
    r"\[SYSTEM\]",
    r"override\s+(?:your\s+)?(?:system|safety)\s+(?:prompt|instructions|rules)",
]

# Words / phrases that are categorically blocked
BLOCKED_TERMS: List[str] = [
    # Add any enterprise-specific block terms here
]


# ─── Internal Checks ─────────────────────────────────────────────────

def _detect_unsafe_action(text: str) -> Optional[str]:
    """
    Scan the message for write/mutate/destructive intent.
    Returns the matched pattern description if unsafe, or None if safe.
    """
    lower_text = text.lower()
    for pattern in UNSAFE_ACTION_PATTERNS:
        match = re.search(pattern, lower_text)
        if match:
            return match.group(0)
    return None


def _check_injection(text: str) -> bool:
    """Returns True if the text looks like a prompt-injection attempt."""
    lower_text = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return True
    return False


def _check_blocked_terms(text: str) -> Optional[str]:
    """Returns the matched blocked term, or None if clean."""
    lower_text = text.lower()
    for term in BLOCKED_TERMS:
        if term.lower() in lower_text:
            return term
    return None


def _check_message_length(text: str) -> bool:
    """Returns True if message is too long."""
    return len(text) > MAX_MESSAGE_LENGTH


class Message(BaseModel):
    role: str
    content: str


def validate_messages(messages: List[Message]) -> GuardrailResult:
    """
    Run the full guardrail suite on incoming messages.

    Checks performed (in order):
    1. Conversation length limit
    2. Per-message length limit
    3. Prompt-injection detection
    4. Blocked-term filtering
    5. ⭐ Unsafe action detection — blocks delete/update/create operations

    Only safe, READ-ONLY queries are allowed through to the AI Agent.
    Returns GuardrailResult(passed=True) if everything is safe.
    """

    # Check 1: Conversation too long
    if len(messages) > MAX_HISTORY_MESSAGES:
        return GuardrailResult(
            passed=False,
            reason=f"Conversation exceeds the maximum of {MAX_HISTORY_MESSAGES} messages. Please start a new chat.",
        )

    # Only validate the latest user message (not the full history)
    latest_user_messages = [m for m in messages if m.role == "user"]
    if not latest_user_messages:
        return GuardrailResult(passed=True)

    latest_text = latest_user_messages[-1].content

    # Check 2: Message length
    if _check_message_length(latest_text):
        return GuardrailResult(
            passed=False,
            reason=f"Your message exceeds the maximum length of {MAX_MESSAGE_LENGTH} characters.",
        )

    # Check 3: Prompt injection
    if _check_injection(latest_text):
        print("🚫 Guardrail BLOCKED: Prompt-injection attempt detected")
        return GuardrailResult(
            passed=False,
            reason="Your message was blocked by our security policy. Please rephrase your question.",
        )

    # Check 4: Blocked terms
    blocked_term = _check_blocked_terms(latest_text)
    if blocked_term:
        print(f"🚫 Guardrail BLOCKED term: {blocked_term}")
        return GuardrailResult(
            passed=False,
            reason="Your message contains content that violates our usage policy.",
        )

    # Check 5: ⭐ UNSAFE ACTION DETECTION
    # Only read-only queries are allowed. Any write/delete/update intent is blocked.
    unsafe_match = _detect_unsafe_action(latest_text)
    if unsafe_match:
        print(f"🚫 Guardrail BLOCKED unsafe action: '{unsafe_match}'")
        return GuardrailResult(
            passed=False,
            reason=(
                "🔒 This action is not permitted. I can only help with **read-only** queries — "
                "searching, finding, and viewing information. "
                "Operations like delete, update, create, or modify are restricted for security reasons."
            ),
            action_type="blocked_write",
        )

    print("✅ Guardrail: Query is safe (read-only) — proceeding")
    return GuardrailResult(passed=True, action_type="read")
