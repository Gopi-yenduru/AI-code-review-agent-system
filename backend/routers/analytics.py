"""
Analytics Router.
Provides endpoints for developer stats, repository stats, and global overview.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.analytics_service import (
    get_developer_stats,
    get_repo_stats,
    get_overview_stats,
)

logger = logging.getLogger("ai_code_review.routers.analytics")

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/developer/{username}",
    summary="Get developer statistics",
    response_model=dict,
)
async def developer_stats(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get comprehensive review statistics for a specific developer."""
    stats = await get_developer_stats(db, username)
    return {
        "success": True,
        "data": stats,
        "error": None,
    }


@router.get(
    "/repo/{repo_name:path}",
    summary="Get repository statistics",
    response_model=dict,
)
async def repo_stats(
    repo_name: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated review statistics for a specific repository."""
    stats = await get_repo_stats(db, repo_name)
    return {
        "success": True,
        "data": stats,
        "error": None,
    }


@router.get(
    "/overview",
    summary="Get global overview statistics",
    response_model=dict,
)
async def overview_stats(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get global statistics for the dashboard overview."""
    stats = await get_overview_stats(db)
    return {
        "success": True,
        "data": stats,
        "error": None,
    }
