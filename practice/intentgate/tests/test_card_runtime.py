from pathlib import Path

import pytest

from intentgate.runtime.card_runtime import CardRuntime
from intentgate.schemas.message import ChannelType
from intentgate.schemas.reply import CardIntent


@pytest.fixture
def runtime() -> CardRuntime:
    cards_dir = Path(__file__).resolve().parents[1] / "cards"
    return CardRuntime(cards_dir)


def test_render_crm_approve(runtime: CardRuntime) -> None:
    intent = CardIntent(
        template="crm_approve",
        slots={
            "orderNo": "20260520001",
            "orderId": "12345",
            "amount": "9800",
            "shopName": "华东店",
            "applicant": "张三",
        },
    )
    body = runtime.render(ChannelType.WECOM, intent)
    assert body["msgtype"] == "template_card"
    card = body["template_card"]
    assert card["card_type"] == "button_interaction"
    assert card["task_id"] == "crm:approve:12345:v1"
    assert len(card["button_list"]) == 2
