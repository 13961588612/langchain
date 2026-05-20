from typing import Any

from intentgate.schemas.reply import CardIntent


class InMemorySessionStore:
    """会话与活跃卡片状态（开发用；生产换 Redis）。"""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._cards: dict[str, dict[str, Any]] = {}

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    def upsert_session(self, session_id: str, data: dict[str, Any]) -> None:
        existing = self._sessions.get(session_id, {})
        existing.update(data)
        self._sessions[session_id] = existing

    def save_card(self, task_id: str, intent: CardIntent, state: str = "pending") -> None:
        self._cards[task_id] = {
            "template": intent.template,
            "task_id": task_id,
            "state": state,
            "slots": intent.slots,
        }

    def get_card(self, task_id: str) -> dict[str, Any] | None:
        return self._cards.get(task_id)

    def update_card_state(self, task_id: str, state: str) -> None:
        if task_id in self._cards:
            self._cards[task_id]["state"] = state
