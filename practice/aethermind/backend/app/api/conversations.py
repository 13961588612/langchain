"""Conversation and chat API routes."""
import asyncio
import json
import uuid
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ChatRequest,
    ChatStreamChunk,
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation thread."""
    # Verify agent exists
    result = await db.execute(
        select(Agent).where(Agent.id == payload.agent_id, Agent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    conversation = Conversation(
        agent_id=payload.agent_id,
        thread_id=str(uuid.uuid4()),
        title=payload.title or "New Conversation",
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


@router.get("", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    agent_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List conversations with optional agent filter."""
    from sqlalchemy import func

    query = select(Conversation)
    if agent_id:
        query = query.where(Conversation.agent_id == agent_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Conversation.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    conversations = result.scalars().all()

    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single conversation."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)
    await db.flush()


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List messages in a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/{conversation_id}/chat")
async def chat_with_agent(
    conversation_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get a streaming response from the agent."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify agent exists and is active
    result = await db.execute(
        select(Agent).where(
            Agent.id == conversation.agent_id,
            Agent.is_deleted == False,
            Agent.is_active == True,
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not found or inactive")

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    await db.flush()

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events for streaming response."""
        try:
            full_response = ""

            # Import here to avoid circular imports
            from app.core.agent_runtime import AgentRuntime

            runtime = AgentRuntime()
            async for chunk in runtime.stream_chat(
                agent_id=agent.id,
                thread_id=conversation.thread_id,
                message=payload.message,
            ):
                event_type = chunk.get("event", "token")
                content = chunk.get("content", "")

                if event_type == "token":
                    full_response += content
                elif event_type == "done":
                    # Save assistant message to database
                    assistant_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response,
                        metadata_=chunk.get("metadata"),
                    )
                    db.add(assistant_msg)
                    await db.flush()
                    await db.commit()

                yield {"event": event_type, "data": json.dumps(chunk)}

        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"content": str(exc), "event": "error"}),
            }

    return EventSourceResponse(event_generator())
