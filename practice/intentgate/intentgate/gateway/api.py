from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from intentgate.adapters.agent_backend import AgentBackend
from intentgate.runtime.card_runtime import CardRuntime
from intentgate.schemas.message import CardActionEvent, ChannelType, StandardMessage
from intentgate.schemas.reply import AgentReply, CardIntent

router = APIRouter(prefix="/api/v1", tags=["gateway"])


class RenderCardRequest(BaseModel):
    channel: ChannelType
    intent: CardIntent


def _card_runtime() -> CardRuntime:
    from intentgate.main import get_card_runtime

    return get_card_runtime()


def _agent_backend() -> AgentBackend:
    from intentgate.main import get_agent_backend

    return get_agent_backend()


@router.post("/messages", response_model=list[AgentReply])
async def ingest_message(
    message: StandardMessage,
    backend: AgentBackend = Depends(_agent_backend),
) -> list[AgentReply]:
    """入站用户消息 → Agent 慢路径。"""
    replies: list[AgentReply] = []
    async for reply in backend.chat(message):
        replies.append(reply)
    return replies


@router.post("/actions", response_model=list[AgentReply])
async def ingest_action(
    event: CardActionEvent,
    backend: AgentBackend = Depends(_agent_backend),
) -> list[AgentReply]:
    """卡片动作：快路径在 Channel Adapter 内处理；此处为慢路径 Agent 回调。"""
    replies: list[AgentReply] = []
    async for reply in backend.handle_action(event):
        replies.append(reply)
    return replies


@router.post("/cards/render")
async def render_card(
    body: RenderCardRequest,
    runtime: CardRuntime = Depends(_card_runtime),
) -> dict:
    """CardIntent → 客户端原生卡片 JSON（调试 / Adapter 共用）。"""
    try:
        return runtime.render(body.channel, body.intent)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/protocol")
async def protocol_spec() -> dict:
    """AgentBackend 与 Gateway 之间的协议摘要。"""
    return {
        "inbound": {
            "StandardMessage": StandardMessage.model_json_schema(),
            "CardActionEvent": CardActionEvent.model_json_schema(),
        },
        "outbound": {
            "AgentReply": AgentReply.model_json_schema(),
            "CardIntent": CardIntent.model_json_schema(),
        },
        "agent_endpoints": {
            "chat": "POST {backend}/v1/sessions/{session_id}/messages  (SSE)",
            "action": "POST {backend}/v1/sessions/{session_id}/actions  (SSE)",
        },
    }
