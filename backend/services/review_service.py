"""
Review orchestration service.
Triggers the multi-agent pipeline, saves results to DB, and updates developer stats.
"""

import json
import logging
from typing import Any
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.graph import run_review_pipeline
from backend.models.review import Review, Issue, AgentType, Severity, ReviewStatus
from backend.models.user import Developer

logger = logging.getLogger("ai_code_review.services.review")

# Map string severity to enum
SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
}


async def run_review(
    db: AsyncSession,
    pr_url: str,
    repo_name: str,
    pr_number: int,
    pr_title: str,
    author: str,
    code_diff: str,
) -> dict[str, Any]:
    """
    Execute the full review pipeline and persist results.
    1. Creates a Review record (status=processing)
    2. Runs the LangGraph multi-agent pipeline
    3. Saves all issues to the database
    4. Updates developer statistics
    5. Returns the review result
    """
    # --- Create initial Review record ---
    review = Review(
        pr_url=pr_url,
        repo_name=repo_name,
        pr_number=pr_number,
        pr_title=pr_title,
        author=author,
        status=ReviewStatus.PROCESSING,
    )
    db.add(review)
    await db.flush()  # Get the ID without committing

    logger.info(f"Created review {review.id} for {repo_name}#{pr_number}")

    try:
        # --- Run the agent pipeline ---
        result = await run_review_pipeline(
            code_diff=code_diff,
            pr_title=pr_title,
            repo_name=repo_name,
        )

        # --- Save issues to DB ---
        security_issues = result.get("security", {}).get("issues", [])
        performance_issues = result.get("performance", {}).get("issues", [])
        quality_data = result.get("quality", {})
        quality_issues = quality_data.get("issues", [])

        # Save security issues
        for issue_data in security_issues:
            issue = Issue(
                review_id=review.id,
                agent_type=AgentType.SECURITY,
                severity=SEVERITY_MAP.get(issue_data.get("severity", "medium"), Severity.MEDIUM),
                description=issue_data.get("description", ""),
                line_number=issue_data.get("line_number"),
                file_path=issue_data.get("file_path"),
                suggestion=issue_data.get("suggestion"),
            )
            db.add(issue)

        # Save performance issues
        for issue_data in performance_issues:
            issue = Issue(
                review_id=review.id,
                agent_type=AgentType.PERFORMANCE,
                severity=SEVERITY_MAP.get(issue_data.get("severity", "medium"), Severity.MEDIUM),
                description=issue_data.get("description", ""),
                line_number=issue_data.get("line_number"),
                file_path=issue_data.get("file_path"),
                suggestion=issue_data.get("suggestion"),
            )
            db.add(issue)

        # Save quality issues
        for issue_data in quality_issues:
            issue = Issue(
                review_id=review.id,
                agent_type=AgentType.QUALITY,
                severity=SEVERITY_MAP.get(issue_data.get("severity", "medium"), Severity.MEDIUM),
                description=issue_data.get("description", ""),
                line_number=issue_data.get("line_number"),
                file_path=issue_data.get("file_path"),
                suggestion=issue_data.get("suggestion"),
            )
            db.add(issue)

        # --- Update Review record ---
        review.overall_risk_score = result.get("overall_risk_score", 0.0)
        review.quality_score = quality_data.get("score")
        review.quality_highlights = json.dumps(quality_data.get("highlights", []))
        review.status = ReviewStatus.COMPLETED
        review.updated_at = datetime.now(timezone.utc)

        # --- Update Developer stats ---
        await _update_developer_stats(
            db=db,
            username=author,
            risk_score=review.overall_risk_score,
            security_issues=security_issues,
            performance_issues=performance_issues,
            quality_issues=quality_issues,
        )

        await db.commit()
        logger.info(f"Review {review.id} completed — risk score: {review.overall_risk_score}")

        return {
            "review_id": str(review.id),
            **result,
        }

    except Exception as e:
        logger.error(f"Review pipeline failed for {repo_name}#{pr_number}: {e}")
        review.status = ReviewStatus.FAILED
        review.updated_at = datetime.now(timezone.utc)
        await db.commit()
        raise


async def _update_developer_stats(
    db: AsyncSession,
    username: str,
    risk_score: float,
    security_issues: list[dict],
    performance_issues: list[dict],
    quality_issues: list[dict],
) -> None:
    """Update or create developer statistics after a review."""
    result = await db.execute(
        select(Developer).where(Developer.github_username == username)
    )
    developer = result.scalar_one_or_none()

    all_issues = security_issues + performance_issues + quality_issues
    critical_count = sum(1 for i in all_issues if i.get("severity") == "critical")
    high_count = sum(1 for i in all_issues if i.get("severity") == "high")
    medium_count = sum(1 for i in all_issues if i.get("severity") == "medium")
    low_count = sum(1 for i in all_issues if i.get("severity") == "low")

    if developer:
        # Update running average
        old_total = developer.total_reviews
        new_total = old_total + 1
        developer.avg_risk_score = (
            (developer.avg_risk_score * old_total + risk_score) / new_total
        )
        developer.total_reviews = new_total
        developer.total_critical_issues += critical_count
        developer.total_high_issues += high_count
        developer.total_medium_issues += medium_count
        developer.total_low_issues += low_count
        developer.updated_at = datetime.now(timezone.utc)
    else:
        # Create new developer record
        developer = Developer(
            github_username=username,
            total_reviews=1,
            avg_risk_score=risk_score,
            total_critical_issues=critical_count,
            total_high_issues=high_count,
            total_medium_issues=medium_count,
            total_low_issues=low_count,
        )
        db.add(developer)

    logger.info(f"Updated stats for @{username}: {developer.total_reviews} reviews, avg risk {developer.avg_risk_score:.1f}")
