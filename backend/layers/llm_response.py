"""
==================  LAYER 6 — LLM (Response Generation)  ==================
Generates a clear, human-readable answer using ONLY the safe,
filtered data that has already passed through the Guardrail,
Secure Retrieval, and PII Masking layers.

The LLM never sees raw user data — it only receives:
  ✅  PII-masked context from the Secure Retrieval layer
  ✅  The conversation history
  ✅  A strict system prompt enforcing grounded answers

After generation, output chunks are PII-masked AGAIN before
reaching the user's browser.

Flow position: PII Masking (on context) → [LLM] → PII Masking (on output) → User
=================================================================================
"""

import ollama
from typing import Generator, List
from pathlib import Path
from layers.pii_masking import mask_pii


# ─── Model Configuration ──────────────────────────────────────
LLM_MODEL = "gpt-oss:120b-cloud"
CHUNK_BUFFER_SIZE = 30  # Characters to buffer before flushing to client

# Load training prompt from external file (if exists)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str, fallback: str) -> str:
    """Load a prompt from the prompts/ directory, fallback to inline."""
    prompt_file = _PROMPTS_DIR / filename
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8").strip()
    return fallback


# Default system prompt — can be overridden via prompts/train_prompt.txt
_DEFAULT_SYSTEM_PROMPT = (
    "You are Nexus intelligence, a strict internal enterprise assistant. "
    "REQUIREMENT 1: You MUST ALWAYS start your response by briefly rephrasing "
    "or repeating the user's question to confirm you understand it. "
    "REQUIREMENT 2: You MUST exclusively answer the user's questions based on "
    "the CONTEXT below. If the answer cannot be found in the CONTEXT, you must "
    "immediately state: 'I cannot find this information inside our connected "
    "SharePoint library.' UNDER NO CIRCUMSTANCES should you answer using your "
    "outside training data, guess, or hallucinate. "
    "REQUIREMENT 3: NEVER reveal, echo, or reproduce any raw PII such as salary, "
    "email addresses, phone numbers, or identification numbers. If the CONTEXT "
    "contains [REDACTED] labels, those values must remain hidden."
)


def _build_system_prompt(context: str) -> dict:
    """Build the full system prompt with injected safe/filtered context."""
    base_prompt = _load_prompt("train_prompt.txt", _DEFAULT_SYSTEM_PROMPT)
    return {
        "role": "system",
        "content": (
            f"{base_prompt}\n\n"
            f"--- ALLOWED CONTEXT (safe, filtered data only) ---\n"
            f"{context}\n"
            f"--- END CONTEXT ---"
        ),
    }


def stream_llm_response(
    messages: List[dict],
    context: str,
) -> Generator[str, None, None]:
    """
    Generate a clear, human-readable answer using only safe and filtered data.

    The LLM receives:
    - A strict system prompt forbidding hallucination and PII leakage
    - PII-masked context from the Secure Retrieval layer
    - The full conversation history

    Each output chunk is PII-masked again before yielding to the user.

    Args:
        messages:  Full conversation history in Ollama format.
        context:   Retrieved data (already PII-masked by upstream layer).

    Yields:
        Chunks of the safe, masked LLM response text.
    """
    try:
        system_prompt = _build_system_prompt(context)

        # Combine system rules with the conversation history
        # The LLM only sees filtered data — never raw PII
        formatted_messages = [system_prompt] + messages

        print(f"🤖 LLM: Generating response from '{LLM_MODEL}' using filtered data only...")

        stream = ollama.chat(
            model=LLM_MODEL,
            messages=formatted_messages,
            stream=True,
        )

        buffer = ""
        for chunk in stream:
            buffer += chunk["message"]["content"]

            # Flush every ~CHUNK_BUFFER_SIZE characters for smooth streaming
            if len(buffer) > CHUNK_BUFFER_SIZE:
                # Double-safety: PII mask the output before it reaches the user
                masked_buffer = mask_pii(buffer)
                yield masked_buffer
                buffer = ""

        # Flush remaining buffer
        if buffer:
            masked_buffer = mask_pii(buffer)
            yield masked_buffer

        print("✅ LLM: Response generation complete.")

    except Exception as e:
        yield f"\n[Backend Error]: {str(e)}"
