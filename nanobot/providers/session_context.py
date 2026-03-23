"""Context variable for propagating session metadata to LLM providers.

The agent loop sets the session key before calling the provider, and the
provider reads it to inject X-Session-Id / X-Turn-Type headers into outgoing
requests — without changing any function signatures in between.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

# Set by AgentLoop._process_message before calling _run_agent_loop.
# Format: "{channel}:{chat_id}:{uuid}" e.g. "telegram:12345:a1b2c3d4"
current_session_key: ContextVar[str | None] = ContextVar("current_session_key", default=None)


class RLSessionTracker:
    """Tracks per-chat RL session IDs, rotating on /new boundaries.

    Each nanobot chat (channel:chat_id) gets a unique RL session ID that
    persists across turns within the same topic.  Calling rotate() generates
    a new UUID suffix so OpenClaw-RL treats subsequent turns as a new session.
    """

    def __init__(self) -> None:
        # chat_key ("{channel}:{chat_id}") -> current RL session ID
        self._sessions: dict[str, str] = {}

    def get(self, chat_key: str) -> str:
        """Get or create the RL session ID for a chat."""
        if chat_key not in self._sessions:
            self._sessions[chat_key] = f"{chat_key}:{uuid.uuid4().hex[:8]}"
        return self._sessions[chat_key]

    def rotate(self, chat_key: str) -> str | None:
        """Rotate the session ID for a chat (called on /new).

        Returns the old session ID (for sending session_done), or None if
        there was no previous session.
        """
        old = self._sessions.pop(chat_key, None)
        self._sessions[chat_key] = f"{chat_key}:{uuid.uuid4().hex[:8]}"
        return old
