"""
GitHub Webhook Router.
Receives webhook events from GitHub, verifies signatures,
and triggers the AI review pipeline for Pull Request events.
"""

import logging
from typing import Any

from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.services.github_service import verify_webhook_signature, get_pr_diff, post_pr_comment
from backend.services.review_service import run_review

logger = logging.getLogger("ai_code_review.routers.webhook")

router = APIRouter(prefix="/webhook", tags=["Webhook"])


async def _process_pr_review(
    pr_url: str,
    repo_name: str,
    pr_number: int,
    pr_title: str,
    author: str,
    db: AsyncSession,
) -> None:
    """Background task to process a Pull Request review."""
    try:
        # Fetch PR diff from GitHub
        code_diff = get_pr_diff(repo_name, pr_number)

        if not code_diff or code_diff.strip() == "":
            logger.warning(f"Empty diff for {repo_name}#{pr_number}, skipping review")
            return

        # Run the multi-agent review pipeline
        result = await run_review(
            db=db,
            pr_url=pr_url,
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_title,
            author=author,
            code_diff=code_diff,
        )

        # Post review comment on the PR
        post_pr_comment(repo_name, pr_number, result)

        logger.info(f"✅ Review complete for {repo_name}#{pr_number}")

    except Exception as e:
        logger.error(f"❌ Review failed for {repo_name}#{pr_number}: {e}")


@router.post(
    "/github",
    summary="GitHub webhook endpoint",
    response_model=dict,
)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Receive and process GitHub webhook events.
    Handles pull_request events (opened, synchronize).
    Verifies HMAC-SHA256 signature before processing.
    """
    settings = get_settings()

    # --- Read raw payload ---
    payload = await request.body()

    # --- Verify webhook signature ---
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_webhook_signature(payload, signature, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # --- Parse event ---
    event_type = request.headers.get("X-GitHub-Event", "")
    data = await request.json()

    logger.info(f"Received webhook: {event_type} — action: {data.get('action', 'N/A')}")

    # --- Handle pull_request events ---
    if event_type == "pull_request":
        action = data.get("action", "")

        # Only process opened and synchronize (new push to PR)
        if action not in ("opened", "synchronize"):
            return {
                "success": True,
                "data": {"message": f"Ignoring pull_request action: {action}"},
                "error": None,
            }

        pr = data.get("pull_request", {})
        repo = data.get("repository", {})

        pr_url = pr.get("html_url", "")
        repo_name = repo.get("full_name", "")
        pr_number = pr.get("number", 0)
        pr_title = pr.get("title", "Untitled PR")
        author = pr.get("user", {}).get("login", "unknown")

        if not repo_name or not pr_number:
            raise HTTPException(status_code=400, detail="Missing repository or PR number")

        logger.info(f"🔍 Processing PR: {repo_name}#{pr_number} by @{author}")

        # Run review in background to avoid webhook timeout
        background_tasks.add_task(
            _process_pr_review,
            pr_url=pr_url,
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_title,
            author=author,
            db=db,
        )

        return {
            "success": True,
            "data": {
                "message": "Review started",
                "repo": repo_name,
                "pr_number": pr_number,
                "author": author,
            },
            "error": None,
        }

    # --- Handle ping event (webhook setup verification) ---
    if event_type == "ping":
        return {
            "success": True,
            "data": {"message": "Pong! Webhook configured successfully."},
            "error": None,
        }

    # --- Ignore other events ---
    return {
        "success": True,
        "data": {"message": f"Event '{event_type}' ignored"},
        "error": None,
    }
