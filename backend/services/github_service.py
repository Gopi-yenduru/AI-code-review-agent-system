"""
GitHub Integration Service.
Handles webhook signature verification, fetching PR diffs,
and posting structured review comments on Pull Requests.
"""

import hmac
import hashlib
import logging
from typing import Any

from github import Github, GithubException

from config import get_settings

logger = logging.getLogger("ai_code_review.services.github")


# ---------------------------------------------------------------------------
# Webhook Signature Verification
# ---------------------------------------------------------------------------

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook HMAC-SHA256 signature.
    Returns True if the signature is valid, False otherwise.
    """
    if not signature or not signature.startswith("sha256="):
        logger.warning("Missing or malformed webhook signature")
        return False

    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    received = signature.removeprefix("sha256=")
    is_valid = hmac.compare_digest(expected, received)

    if not is_valid:
        logger.warning("Webhook signature verification failed")

    return is_valid


# ---------------------------------------------------------------------------
# PR Diff Fetching
# ---------------------------------------------------------------------------

def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """
    Fetch the full code diff for a Pull Request via GitHub API.
    Returns the diff as a string.
    """
    settings = get_settings()

    try:
        g = Github(settings.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Get all changed files and their patches
        files = pr.get_files()
        diff_parts = []

        for file in files:
            if file.patch:
                diff_parts.append(
                    f"--- a/{file.filename}\n"
                    f"+++ b/{file.filename}\n"
                    f"{file.patch}"
                )

        full_diff = "\n\n".join(diff_parts)

        # Truncate very large diffs to stay within LLM context limits
        max_chars = 30000
        if len(full_diff) > max_chars:
            full_diff = full_diff[:max_chars] + "\n\n... [diff truncated due to size]"
            logger.warning(f"Diff for {repo_name}#{pr_number} truncated to {max_chars} chars")

        logger.info(f"Fetched diff for {repo_name}#{pr_number}: {len(full_diff)} chars")
        return full_diff

    except GithubException as e:
        logger.error(f"GitHub API error fetching diff: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching PR diff: {e}")
        raise


# ---------------------------------------------------------------------------
# PR Comment Posting
# ---------------------------------------------------------------------------

def format_review_comment(review_result: dict[str, Any]) -> str:
    """
    Format the multi-agent review result into a structured GitHub PR comment.
    Includes risk score badge, issue tables, and agent summaries.
    """
    risk_score = review_result.get("overall_risk_score", 0)
    security = review_result.get("security", {})
    performance = review_result.get("performance", {})
    quality = review_result.get("quality", {})

    # Risk badge color
    if risk_score >= 75:
        badge = "🔴"
        risk_label = "CRITICAL"
    elif risk_score >= 50:
        badge = "🟠"
        risk_label = "HIGH"
    elif risk_score >= 25:
        badge = "🟡"
        risk_label = "MEDIUM"
    else:
        badge = "🟢"
        risk_label = "LOW"

    # Build comment
    lines = [
        f"## {badge} AI Code Review — Risk Score: {risk_score}/100 ({risk_label})",
        "",
    ]

    # --- Critical Issues Table ---
    all_issues = []
    for issue in security.get("issues", []):
        all_issues.append({**issue, "agent": "🔒 Security"})
    for issue in performance.get("issues", []):
        all_issues.append({**issue, "agent": "⚡ Performance"})
    for issue in quality.get("issues", []):
        all_issues.append({**issue, "agent": "📋 Quality"})

    critical_issues = [i for i in all_issues if i.get("severity") in ("critical", "high")]

    if critical_issues:
        lines.append("### 🚨 Critical & High Severity Issues")
        lines.append("")
        lines.append("| Agent | Severity | Description | Line | Suggestion |")
        lines.append("|-------|----------|-------------|------|------------|")
        for issue in critical_issues:
            sev = issue.get("severity", "").upper()
            desc = issue.get("description", "")[:80]
            line = issue.get("line_number", "—")
            sugg = issue.get("suggestion", "")[:80]
            lines.append(f"| {issue['agent']} | **{sev}** | {desc} | {line} | {sugg} |")
        lines.append("")

    # --- Security Agent Summary ---
    sec_issues = security.get("issues", [])
    lines.append("<details>")
    lines.append(f"<summary>🔒 Security Auditor — {len(sec_issues)} issue(s)</summary>")
    lines.append("")
    if sec_issues:
        for issue in sec_issues:
            sev = issue.get("severity", "unknown").upper()
            lines.append(f"- **[{sev}]** {issue.get('description', '')}")
            if issue.get("suggestion"):
                lines.append(f"  - 💡 {issue['suggestion']}")
    else:
        lines.append("✅ No security issues found.")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # --- Performance Agent Summary ---
    perf_issues = performance.get("issues", [])
    lines.append("<details>")
    lines.append(f"<summary>⚡ Performance Analyst — {len(perf_issues)} issue(s)</summary>")
    lines.append("")
    if perf_issues:
        for issue in perf_issues:
            sev = issue.get("severity", "unknown").upper()
            lines.append(f"- **[{sev}]** {issue.get('description', '')}")
            if issue.get("suggestion"):
                lines.append(f"  - 💡 {issue['suggestion']}")
    else:
        lines.append("✅ No performance issues found.")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # --- Quality Agent Summary ---
    quality_score = quality.get("score", "N/A")
    quality_issues = quality.get("issues", [])
    highlights = quality.get("highlights", [])
    lines.append("<details>")
    lines.append(f"<summary>📋 Code Quality — Score: {quality_score}/100 | {len(quality_issues)} issue(s)</summary>")
    lines.append("")
    if highlights:
        lines.append("**✨ Highlights:**")
        for h in highlights:
            lines.append(f"- {h}")
        lines.append("")
    if quality_issues:
        lines.append("**Issues:**")
        for issue in quality_issues:
            sev = issue.get("severity", "unknown").upper()
            lines.append(f"- **[{sev}]** {issue.get('description', '')}")
            if issue.get("suggestion"):
                lines.append(f"  - 💡 {issue['suggestion']}")
    else:
        lines.append("✅ No quality issues found.")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("*Reviewed by [AI Code Review Agent](https://github.com) — "
                  "Security • Performance • Quality*")

    return "\n".join(lines)


def post_pr_comment(repo_name: str, pr_number: int, review_result: dict[str, Any]) -> bool:
    """
    Post a formatted review comment on a GitHub Pull Request.
    Returns True if successful, False otherwise.
    """
    settings = get_settings()

    try:
        g = Github(settings.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        comment_body = format_review_comment(review_result)
        pr.create_issue_comment(comment_body)

        logger.info(f"Posted review comment on {repo_name}#{pr_number}")
        return True

    except GithubException as e:
        logger.error(f"Failed to post PR comment: {e}")
        return False
    except Exception as e:
        logger.error(f"Error posting PR comment: {e}")
        return False
