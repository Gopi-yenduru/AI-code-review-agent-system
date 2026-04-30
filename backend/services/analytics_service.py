"""
Analytics Service.
Aggregates metrics for the dashboard including developer stats,
repository stats, and global overview statistics.
"""

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.review import Review, Issue, AgentType, Severity, ReviewStatus
from models.user import Developer

logger = logging.getLogger("ai_code_review.services.analytics")


async def get_developer_stats(db: AsyncSession, username: str) -> dict[str, Any]:
    """
    Get comprehensive statistics for a developer.
    Includes avg risk score over time, most common issue types, and trend.
    """
    # Get developer record
    result = await db.execute(
        select(Developer).where(Developer.github_username == username)
    )
    developer = result.scalar_one_or_none()

    if not developer:
        return {
            "username": username,
            "found": False,
            "total_reviews": 0,
            "avg_risk_score": 0.0,
            "reviews": [],
            "issue_breakdown": {},
            "trend": [],
        }

    # Get all reviews by this author
    reviews_result = await db.execute(
        select(Review)
        .where(
            and_(
                Review.author == username,
                Review.status == ReviewStatus.COMPLETED,
            )
        )
        .order_by(desc(Review.created_at))
    )
    reviews = reviews_result.scalars().all()

    # Build review list with risk scores for trend chart
    trend_data = [
        {
            "review_id": str(r.id),
            "pr_title": r.pr_title,
            "repo_name": r.repo_name,
            "risk_score": r.overall_risk_score or 0,
            "quality_score": r.quality_score or 0,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]

    # Issue breakdown by severity
    issue_breakdown = {
        "critical": developer.total_critical_issues,
        "high": developer.total_high_issues,
        "medium": developer.total_medium_issues,
        "low": developer.total_low_issues,
    }

    # Get most common issue descriptions for this developer
    issues_result = await db.execute(
        select(Issue.description, Issue.agent_type, func.count(Issue.id).label("count"))
        .join(Review, Issue.review_id == Review.id)
        .where(Review.author == username)
        .group_by(Issue.description, Issue.agent_type)
        .order_by(desc("count"))
        .limit(10)
    )
    frequent_issues = [
        {
            "description": row.description[:100],
            "agent_type": row.agent_type.value,
            "count": row.count,
        }
        for row in issues_result
    ]

    return {
        "username": username,
        "found": True,
        "total_reviews": developer.total_reviews,
        "avg_risk_score": round(developer.avg_risk_score, 1),
        "issue_breakdown": issue_breakdown,
        "frequent_issues": frequent_issues,
        "trend": trend_data,
    }


async def get_repo_stats(db: AsyncSession, repo_name: str) -> dict[str, Any]:
    """Get aggregated statistics for a repository."""
    # Count reviews
    count_result = await db.execute(
        select(func.count(Review.id))
        .where(
            and_(
                Review.repo_name == repo_name,
                Review.status == ReviewStatus.COMPLETED,
            )
        )
    )
    total_reviews = count_result.scalar() or 0

    # Average risk score
    avg_result = await db.execute(
        select(func.avg(Review.overall_risk_score))
        .where(
            and_(
                Review.repo_name == repo_name,
                Review.status == ReviewStatus.COMPLETED,
            )
        )
    )
    avg_risk = avg_result.scalar() or 0.0

    # Top issues in this repo
    issues_result = await db.execute(
        select(
            Issue.severity,
            Issue.agent_type,
            func.count(Issue.id).label("count"),
        )
        .join(Review, Issue.review_id == Review.id)
        .where(Review.repo_name == repo_name)
        .group_by(Issue.severity, Issue.agent_type)
        .order_by(desc("count"))
        .limit(10)
    )
    top_issues = [
        {
            "severity": row.severity.value,
            "agent_type": row.agent_type.value,
            "count": row.count,
        }
        for row in issues_result
    ]

    # Recent reviews
    recent_result = await db.execute(
        select(Review)
        .where(Review.repo_name == repo_name)
        .order_by(desc(Review.created_at))
        .limit(10)
    )
    recent_reviews = [
        {
            "review_id": str(r.id),
            "pr_title": r.pr_title,
            "pr_number": r.pr_number,
            "author": r.author,
            "risk_score": r.overall_risk_score or 0,
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_result.scalars()
    ]

    return {
        "repo_name": repo_name,
        "total_reviews": total_reviews,
        "avg_risk_score": round(avg_risk, 1),
        "top_issues": top_issues,
        "recent_reviews": recent_reviews,
    }


async def get_overview_stats(db: AsyncSession) -> dict[str, Any]:
    """Get global statistics for the dashboard overview."""
    # Total reviews
    total_result = await db.execute(
        select(func.count(Review.id))
        .where(Review.status == ReviewStatus.COMPLETED)
    )
    total_reviews = total_result.scalar() or 0

    # Average risk score
    avg_result = await db.execute(
        select(func.avg(Review.overall_risk_score))
        .where(Review.status == ReviewStatus.COMPLETED)
    )
    avg_risk = avg_result.scalar() or 0.0

    # Total critical issues
    critical_result = await db.execute(
        select(func.count(Issue.id))
        .where(Issue.severity == Severity.CRITICAL)
    )
    total_critical = critical_result.scalar() or 0

    # Reviews last 30 days (for trend chart)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    trend_result = await db.execute(
        select(
            func.date(Review.created_at).label("date"),
            func.count(Review.id).label("count"),
            func.avg(Review.overall_risk_score).label("avg_risk"),
        )
        .where(
            and_(
                Review.created_at >= thirty_days_ago,
                Review.status == ReviewStatus.COMPLETED,
            )
        )
        .group_by(func.date(Review.created_at))
        .order_by("date")
    )
    daily_trend = [
        {
            "date": str(row.date),
            "count": row.count,
            "avg_risk": round(float(row.avg_risk or 0), 1),
        }
        for row in trend_result
    ]

    # Top issues this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_issues_result = await db.execute(
        select(
            Issue.agent_type,
            Issue.severity,
            func.count(Issue.id).label("count"),
        )
        .join(Review, Issue.review_id == Review.id)
        .where(Review.created_at >= week_ago)
        .group_by(Issue.agent_type, Issue.severity)
        .order_by(desc("count"))
        .limit(10)
    )
    weekly_issues = [
        {
            "agent_type": row.agent_type.value,
            "severity": row.severity.value,
            "count": row.count,
        }
        for row in weekly_issues_result
    ]

    # Recent reviews
    recent_result = await db.execute(
        select(Review)
        .where(Review.status == ReviewStatus.COMPLETED)
        .order_by(desc(Review.created_at))
        .limit(20)
    )
    recent_reviews = [
        {
            "review_id": str(r.id),
            "pr_title": r.pr_title,
            "pr_number": r.pr_number,
            "repo_name": r.repo_name,
            "author": r.author,
            "risk_score": r.overall_risk_score or 0,
            "quality_score": r.quality_score or 0,
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_result.scalars()
    ]

    return {
        "total_reviews": total_reviews,
        "avg_risk_score": round(avg_risk, 1),
        "total_critical_issues": total_critical,
        "daily_trend": daily_trend,
        "weekly_issues": weekly_issues,
        "recent_reviews": recent_reviews,
    }
