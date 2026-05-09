"""Conversation and message schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    agent_id: str = Field(..., description="Agent ID")
    title: Optional[str] = Field(None, max_length=500)


class ConversationResponse(BaseModel):
    """Schema for conversation API response."""

    id: str
    agent_id: str
    thread_id: str
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for sending a message."""

    content: str = Field(..., min_length=1)
    role: str = Field("user", pattern="^(user)$")


class MessageResponse(BaseModel):
    """Schema for message API response."""

    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat/completion request."""

    message: str = Field(..., min_length=1, description="User message content")
    thread_id: Optional[str] = Field(None, description="Existing thread ID for continuation")


class ChatStreamChunk(BaseModel):
    """Schema for a single streaming chat chunk."""

    content: str = ""
    event: str = "token"  # token / tool_call / tool_result / done / error
    metadata: Optional[dict] = None
