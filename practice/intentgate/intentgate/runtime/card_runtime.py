from pathlib import Path
from typing import Any

import yaml

from intentgate.runtime.renderers.base import CardRenderer
from intentgate.runtime.renderers.wecom import WeComRenderer
from intentgate.schemas.message import ChannelType
from intentgate.schemas.reply import CardIntent


class CardRuntime:
    """加载 YAML 模板，渲染 CardIntent 为通道原生格式。"""

    def __init__(self, cards_dir: Path) -> None:
        self._cards_dir = cards_dir
        self._renderers: dict[ChannelType, CardRenderer] = {
            ChannelType.WECOM: WeComRenderer(),
        }

    def load_template(self, name: str) -> dict[str, Any]:
        path = self._cards_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Card template not found: {path}")
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    def render(self, channel: ChannelType, intent: CardIntent) -> dict[str, Any]:
        template_def = self.load_template(intent.template)
        renderer = self._renderers.get(channel)
        if renderer is None:
            raise ValueError(f"No renderer for channel: {channel}")
        return renderer.render(intent, template_def)
