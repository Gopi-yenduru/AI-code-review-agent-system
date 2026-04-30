"""
Reviews Router.
Provides endpoints for listing and viewing code review results.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.review import Review, Issue, ReviewStatus

logger = logging.getLogger("ai_code_review.routers.reviews")

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "",
    summary="List reviews with pagination and filters",
    response_model=dict,
)
async def list_reviews(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    repo: Optional[str] = Query(default=None, description="Filter by repository"),
    author: Optional[str] = Query(default=None, description="Filter by author"),
    min_risk: Optional[float] = Query(default=None, ge=0, le=100, description="Minimum risk score"),
    max_risk: Optional[float] = Query(default=None, ge=0, le=100, description="Maximum risk score"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a paginated list of code reviews with optional filters."""
    # Build query
    query = select(Review)
    count_query = select(func.count(Review.id))

    filters = []
    if repo:
        filters.append(Review.repo_name == repo)
    if author:
        filters.append(Review.author == author)
    if min_risk is not None:
        filters.append(Review.overall_risk_score >= min_risk)
    if max_risk is not None:
        filters.append(Review.overall_risk_score <= max_risk)
    if status:
        try:
            filters.append(Review.status == ReviewStatus(status))
        except ValueError:
            pass

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(desc(Review.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    reviews = result.scalars().all()

    reviews_data = [
        {
            "id": str(r.id),
            "pr_url": r.pr_url,
            "repo_name": r.repo_name,
            "pr_number": r.pr_number,
            "pr_title": r.pr_title,
            "author": r.author,
            "overall_risk_score": r.overall_risk_score,
            "quality_score": r.quality_score,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
            "issue_count": len(r.issues) if r.issues else 0,
        }
        for r in reviews
    ]

    return {
        "success": True,
        "data": {
            "reviews": reviews_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
        "error": None,
    }


@router.get(
    "/{review_id}",
    summary="Get review details",
    response_model=dict,
)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get full details of a single review including all issues."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Group issues by agent type
    security_issues = []
    performance_issues = []
    quality_issues = []

    for issue in review.issues:
        issue_data = {
            "id": str(issue.id),
            "severity": issue.severity.value,
            "description": issue.description,
            "line_number": issue.line_number,
            "file_path": issue.file_path,
            "suggestion": issue.suggestion,
        }
        if issue.agent_type.value == "security":
            security_issues.append(issue_data)
        elif issue.agent_type.value == "performance":
            performance_issues.append(issue_data)
        elif issue.agent_type.value == "quality":
            quality_issues.append(issue_data)

    import json
    highlights = []
    if review.quality_highlights:
        try:
            highlights = json.loads(review.quality_highlights)
        except json.JSONDecodeError:
            highlights = []

    return {
        "success": True,
        "data": {
            "id": str(review.id),
            "pr_url": review.pr_url,
            "repo_name": review.repo_name,
            "pr_number": review.pr_number,
            "pr_title": review.pr_title,
            "author": review.author,
            "overall_risk_score": review.overall_risk_score,
            "quality_score": review.quality_score,
            "quality_highlights": highlights,
            "status": review.status.value,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat(),
            "agents": {
                "security": {
                    "issues": security_issues,
                    "count": len(security_issues),
                },
                "performance": {
                    "issues": performance_issues,
                    "count": len(performance_issues),
                },
                "quality": {
                    "issues": quality_issues,
                    "count": len(quality_issues),
                    "score": review.quality_score,
                    "highlights": highlights,
                },
            },
            "total_issues": len(review.issues),
        },
        "error": None,
    }
