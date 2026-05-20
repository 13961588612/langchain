import re
from typing import Any

from intentgate.runtime.renderers.base import CardRenderer
from intentgate.schemas.message import ChannelType
from intentgate.schemas.reply import CardIntent


def _fill(template: str, slots: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(slots.get(key, match.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", repl, template)


class WeComRenderer(CardRenderer):
    channel = ChannelType.WECOM

    def render(self, intent: CardIntent, template_def: dict[str, Any]) -> dict[str, Any]:
        card_type = template_def.get("template", intent.template)
        slots = {**template_def.get("slots", {}), **intent.slots}

        main_title = {
            "title": _fill(str(slots.get("title", "")), slots),
            "desc": _fill(str(slots.get("desc", "")), slots),
        }

        body: dict[str, Any] = {
            "msgtype": "template_card",
            "template_card": {
                "card_type": card_type,
                "main_title": main_title,
            },
        }

        rows = template_def.get("rows") or slots.get("rows")
        if rows:
            body["template_card"]["horizontal_content_list"] = [
                {
                    "keyname": _fill(str(r["keyname"]), slots),
                    "value": _fill(str(r["value"]), slots),
                }
                for r in rows
            ]

        buttons = intent.actions or template_def.get("buttons", [])
        if buttons and card_type == "button_interaction":
            body["template_card"]["button_list"] = [
                {
                    "text": b.label if hasattr(b, "label") else b.get("text", ""),
                    "key": b.key if hasattr(b, "key") else b.get("key", ""),
                    "style": b.style if hasattr(b, "style") else b.get("style", 1),
                }
                for b in buttons
            ]

        task_id_tpl = template_def.get("task_id") or intent.task_id
        if task_id_tpl:
            body["template_card"]["task_id"] = _fill(str(task_id_tpl), slots)

        return body
