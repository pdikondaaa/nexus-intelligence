/**
 * ============================================================
 *  API Service Layer
 * ============================================================
 *  Centralises all HTTP communication with the Python backend.
 *  The Chat UI calls these functions instead of using raw fetch.
 * ============================================================
 */

const API_BASE = 'http://127.0.0.1:8000';

/**
 * Send a chat request and return a streaming ReadableStreamDefaultReader.
 *
 * @param {Array<{role:string, content:string}>} messages  Conversation history
 * @param {string} accessToken  Microsoft bearer token (may be empty)
 * @returns {Promise<ReadableStreamDefaultReader>}
 */
export async function sendChatMessage(messages, accessToken = '') {
  const headers = { 'Content-Type': 'application/json' };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ messages }),
  });

  // If the guardrail layer rejected the message, surface its reason
  if (response.status === 400) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Request was blocked by security policy.');
  }

  if (!response.ok) {
    throw new Error(`Network error: ${response.status} ${response.statusText}`);
  }

  return response.body.getReader();
}
