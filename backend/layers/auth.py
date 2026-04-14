"""
========================  LAYER 1 — AUTH  ========================
Validates the incoming request's Authorization header and extracts
the user identity + access token for downstream permission-based
data retrieval.

Flow position: Chat UI → [Auth Layer] → Security Guardrail
=================================================================
"""

from fastapi import Request, HTTPException
import base64
import json
from typing import Optional


# 🚨 Development-only hardcoded token — replace with real token or remove in production
HARDCODED_GRAPH_TOKEN: str = ""

class AuthResult:
    """Carries verified identity + token through the rest of the pipeline."""

    def __init__(
        self,
        access_token: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        self.access_token = access_token
        self.user_name = user_name
        self.user_email = user_email
        self.tenant_id = tenant_id

    def __repr__(self):
        return f"AuthResult(user={self.user_name}, email={self.user_email})"


def _decode_jwt_claims(token: str) -> dict:
    """
    Decode the payload section of a JWT without verification
    (verification is handled by Azure AD at the API gateway level).
    This is used purely for extracting display-name / email metadata.
    """
    try:
        payload_segment = token.split(".")[1]
        # JWT base64 may need padding
        padding = 4 - len(payload_segment) % 4
        if padding != 4:
            payload_segment += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_segment)
        return json.loads(decoded)
    except Exception:
        return {}


def authenticate_request(request: Request) -> AuthResult:
    """
    Extract and validate the bearer token from the request.

    Priority:
    1. Hardcoded dev token (if set and non-empty)
    2. Authorization header from the React frontend

    Returns an AuthResult or raises HTTPException(401).
    """

    access_token: Optional[str] = None

    # Priority 1: Hardcoded dev token
    if HARDCODED_GRAPH_TOKEN:
        access_token = HARDCODED_GRAPH_TOKEN

    # Priority 2: Frontend-supplied bearer token
    if not access_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ", 1)[1]

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in with Microsoft.",
        )

    # Extract user metadata from the JWT payload
    claims = _decode_jwt_claims(access_token)
    user_name = claims.get("name")
    user_email = claims.get("upn") or claims.get("unique_name")
    tenant_id = claims.get("tid")

    print(f"🔐 Authenticated: {user_name} ({user_email})")

    return AuthResult(
        access_token=access_token,
        user_name=user_name,
        user_email=user_email,
        tenant_id=tenant_id,
    )
