"""Agent CRUD API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentListItem, AgentResponse, AgentUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent."""
    agent = Agent(
        name=payload.name,
        description=payload.description,
        system_prompt=payload.system_prompt,
        model_provider=payload.model_provider,
        model_name=payload.model_name,
        model_parameters=payload.model_parameters,
        api_key_ref=payload.api_key_ref,
        soul_config=payload.soul_config,
        profile_config=payload.profile_config,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.get("", response_model=PaginatedResponse[AgentListItem])
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or description"),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List agents with pagination and filtering."""
    query = select(Agent).where(Agent.is_deleted == False)

    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    if search:
        query = query.where(
            (Agent.name.ilike(f"%{search}%"))
            | (Agent.description.ilike(f"%{search}%"))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Agent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()

    pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=[AgentListItem.model_validate(a) for a in agents],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single agent by ID."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)

    await db.flush()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_deleted = True
    agent.is_active = False
    await db.flush()


@router.post("/{agent_id}/activate", response_model=AgentResponse)
async def toggle_agent_active(
    agent_id: str,
    active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = active
    await db.flush()
    await db.refresh(agent)
    return agent
