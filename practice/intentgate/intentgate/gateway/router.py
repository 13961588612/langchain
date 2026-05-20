from intentgate.schemas.message import CardActionEvent

# 快路径：无需 Agent 即可处理的按钮 key
FAST_PATH_ACTIONS: frozenset[str] = frozenset({"approve", "reject", "confirm", "cancel", "page_next", "page_prev"})


def is_fast_path(event: CardActionEvent) -> bool:
    return event.action_key in FAST_PATH_ACTIONS
