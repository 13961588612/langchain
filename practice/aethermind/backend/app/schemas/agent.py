"""Agent schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    model_provider: str = Field("openai", description="Model provider: openai/anthropic/google/ollama")
    model_name: str = Field("gpt-4o", description="Model name")
    model_parameters: Optional[str] = Field(
        None, description="JSON string of model parameters"
    )
    api_key_ref: Optional[str] = Field(None, description="Reference to stored API key")
    soul_config: Optional[str] = Field(None, description="Soul/personality config YAML")
    profile_config: Optional[str] = Field(None, description="Profile/behavior config YAML")


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_parameters: Optional[str] = None
    api_key_ref: Optional[str] = None
    soul_config: Optional[str] = None
    profile_config: Optional[str] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent API response."""

    id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_provider: str
    model_name: str
    model_parameters: Optional[str] = None
    is_active: bool
    soul_config: Optional[str] = None
    profile_config: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListItem(BaseModel):
    """Schema for agent in list view (lightweight)."""

    id: str
    name: str
    description: Optional[str] = None
    model_provider: str
    model_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
