"""
=============  LAYER 4 — SECURE RETRIEVAL (Data Layer)  =============
Fetches data from sources based on user access. Uses the authenticated
user's own token to ensure results respect their permissions.
The user ONLY sees documents they are authorised to access.

Flow position: AI Agent → [Secure Retrieval] → PII Masking
=====================================================================
"""

import requests
from typing import Optional
from layers.auth import AuthResult


# ─── SharePoint Configuration ─────────────────────────────────
SHAREPOINT_SITE_URL = "https://alignedautomation.sharepoint.com/sites/Nexus"
MAX_RESULTS = 5  # Top-N search results to inject as context


def _clean_highlight_tags(text: str) -> str:
    """Strip SharePoint-specific highlight markup from summaries."""
    return (
        text.replace("<c0>", "")
        .replace("</c0>", "")
        .replace("<ddd/>", "")
        .strip()
    )


def fetch_data(query: str, data_source: str, auth: AuthResult) -> str:
    """
    Secure data retrieval dispatcher.

    Routes to the appropriate data source based on the AI Agent's
    decision. Currently supports:
      - "sharepoint" → SharePoint Online search
      - "none"       → No retrieval needed

    Future sources can be added here (databases, APIs, file shares, etc.)
    without changing any other layer.

    Args:
        query:        Optimized search keywords from the AI Agent.
        data_source:  Which source to query (decided by the Agent).
        auth:         AuthResult carrying the user's access token.

    Returns:
        A formatted context string of retrieved results.
    """
    if data_source == "none":
        return ""

    if data_source == "sharepoint":
        return _search_sharepoint(query, auth)

    # ─── Future data sources can be plugged in here ───────────
    # if data_source == "sql_database":
    #     return _query_database(query, auth)
    # if data_source == "confluence":
    #     return _search_confluence(query, auth)

    print(f"⚠️  Retrieval: Unknown data source '{data_source}' — skipping")
    return f"[Unknown data source: {data_source}]"


def _search_sharepoint(query: str, auth: AuthResult) -> str:
    """
    Search SharePoint Online using the user's own access token.
    This guarantees **permission-based** retrieval — users only see
    documents they actually have access to.

    Args:
        query:  Optimized search keywords from the AI Agent layer.
        auth:   AuthResult carrying the user's access token.

    Returns:
        A formatted context string of search results, or a fallback
        message if nothing was found.
    """

    if not auth.access_token:
        return "[SharePoint Context unavailable. No valid authentication token.]"

    print(f"🔍 Secure Retrieval: Searching SharePoint for '{query}' (user: {auth.user_name})...")

    query_text = f'{query} path:"{SHAREPOINT_SITE_URL}"'
    search_url = f"{SHAREPOINT_SITE_URL}/_api/search/query?querytext='{query_text}'"

    headers = {
        "Authorization": f"Bearer {auth.access_token}",
        "Accept": "application/json;odata=nometadata",
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=15)

        if response.status_code == 401:
            print("🔒 Secure Retrieval: Token expired or insufficient permissions")
            return "[Access denied. Your session may have expired — please sign in again.]"

        if response.status_code == 403:
            print("🔒 Secure Retrieval: User does not have permission to this resource")
            return "[You do not have permission to access this resource.]"

        if response.status_code != 200:
            print(f"❌ Secure Retrieval: SharePoint API error {response.status_code}")
            return f"[SharePoint returned error {response.status_code}.]"

        results = response.json()

        # Robust OData unwrapping for SharePoint Online
        if "d" in results and "query" in results["d"]:
            results = results["d"]["query"]

        rows = (
            results.get("PrimaryQueryResult", {})
            .get("RelevantResults", {})
            .get("Table", {})
            .get("Rows", [])
        )
        if isinstance(rows, dict) and "results" in rows:
            rows = rows["results"]

        extracted_text = []
        for row in rows[:MAX_RESULTS]:
            cells = row.get("Cells", [])
            if isinstance(cells, dict) and "results" in cells:
                cells = cells["results"]

            title = "Unknown Document"
            summary = ""
            path = ""
            description = ""

            for cell in cells:
                key = cell.get("Key")
                val = cell.get("Value") or ""
                if key == "Title":
                    title = val
                elif key == "HitHighlightedSummary":
                    summary = val
                elif key == "Path":
                    path = val
                elif key == "Description":
                    description = val

            clean_summary = _clean_highlight_tags(summary or description)
            extracted_text.append(
                f"Source [{title}]: {clean_summary} (Location: {path})"
            )

        if extracted_text:
            print(
                f"✅ Secure Retrieval: {len(extracted_text)} results found "
                f"(scoped to {auth.user_name}'s permissions)"
            )
            return "\n\n".join(extracted_text)
        else:
            return "[No relevant SharePoint documents found for this query.]"

    except requests.exceptions.Timeout:
        print("⏳ Secure Retrieval: SharePoint search timed out.")
        return "[SharePoint search timed out. Please try again.]"
    except Exception as err:
        print(f"❌ Secure Retrieval: Failed to reach SharePoint — {err}")
        return "[Failed to connect to SharePoint Search API.]"
