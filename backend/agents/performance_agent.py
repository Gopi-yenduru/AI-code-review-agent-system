"""
Performance Analyst Agent.
Analyzes code diffs for performance issues including N+1 queries,
inefficient loops, unnecessary DB calls, high complexity, and memory leaks.
"""

import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from agents.output_parsing import parse_json_object, normalize_issue
from config import get_settings

logger = logging.getLogger("ai_code_review.agents.performance")

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

PERFORMANCE_SYSTEM_PROMPT = """You are an expert Performance Analyst AI Agent specializing in code review.
Your task is to analyze code diffs from Pull Requests and identify performance issues.

## Your Focus Areas
1. **N+1 Query Patterns** — Database queries inside loops, missing eager loading, repeated single-row fetches
2. **Inefficient Loops** — O(n²) or worse algorithms where O(n) or O(n log n) solutions exist
3. **Unnecessary Database Calls** — Redundant queries, missing caching, fetching unused columns
4. **High Time Complexity** — Nested iterations over large datasets, unoptimized search/sort
5. **Memory Leaks** — Unbounded list growth, missing cleanup, large objects in long-lived scopes
6. **Blocking Operations** — Synchronous I/O in async context, CPU-bound work blocking event loop
7. **Missing Pagination** — Fetching all records without LIMIT, loading entire tables into memory
8. **Inefficient String Operations** — String concatenation in loops, repeated regex compilation

## Output Format
You MUST return ONLY valid JSON. No markdown formatting, no code fences, no explanations outside JSON.

Return this exact JSON structure:
{
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "description": "Clear description of the performance issue",
            "line_number": 15,
            "file_path": "path/to/file.py",
            "suggestion": "Specific performance improvement recommendation",
            "estimated_impact": "Brief description of expected performance improvement"
        }
    ]
}

## Severity Guidelines
- **critical**: Severe performance bottleneck that will cause outages under load (unbounded queries, memory leaks in hot paths)
- **high**: Significant performance issue affecting user experience (N+1 queries, O(n²) on large datasets)
- **medium**: Performance concern that may impact scalability
- **low**: Minor optimization opportunity or best practice

## Few-Shot Examples

### Example Input:
```diff
+ async def get_all_users_with_orders():
+     users = await db.execute(select(User))
+     result = []
+     for user in users.scalars():
+         orders = await db.execute(
+             select(Order).where(Order.user_id == user.id)
+         )
+         result.append({"user": user, "orders": orders.scalars().all()})
+     return result
```

### Example Output:
{
    "issues": [
        {
            "severity": "high",
            "description": "N+1 query pattern detected. For each user, a separate database query fetches their orders. With 1000 users, this executes 1001 queries.",
            "line_number": 5,
            "file_path": null,
            "suggestion": "Use SQLAlchemy's selectinload or joinedload for eager loading: select(User).options(selectinload(User.orders))",
            "estimated_impact": "Reduces N+1 queries to 2 queries regardless of user count. ~100x improvement for 100 users."
        }
    ]
}

### Example Input (Clean Code):
```diff
+ users = await db.execute(
+     select(User).options(selectinload(User.orders)).limit(50)
+ )
```

### Example Output:
{
    "issues": []
}

## Rules
- Only report genuine performance issues — not style preferences
- Quantify impact when possible (e.g., "O(n²) → O(n)", "1001 queries → 2 queries")
- Always provide actionable suggestions with code examples
- Consider the realistic scale of data when assessing severity
- If no performance issues are found, return {"issues": []}
- Return ONLY the JSON object, nothing else
"""


# ---------------------------------------------------------------------------
# Agent Function
# ---------------------------------------------------------------------------

async def run_performance_agent(code_diff: str, pr_title: str, repo_name: str) -> dict[str, Any]:
    """
    Run the Performance Analyst agent on a code diff.
    Returns a dict with 'issues' list containing performance findings.
    """
    settings = get_settings()

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )

        messages = [
            SystemMessage(content=PERFORMANCE_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"## Pull Request\n"
                f"**Title:** {pr_title}\n"
                f"**Repository:** {repo_name}\n\n"
                f"## Code Diff to Analyze\n"
                f"```diff\n{code_diff}\n```\n\n"
                f"Analyze this code diff for performance issues. "
                f"Return ONLY valid JSON."
            )),
        ]

        response = await llm.ainvoke(messages)
        result = parse_json_object(response.content)

        # A response without an issues list is malformed, not "no issues found"
        issues = result.get("issues")
        if not isinstance(issues, list):
            raise ValueError("Response is missing an 'issues' list")

        validated_issues = []
        for raw_issue in issues:
            issue = normalize_issue(
                raw_issue,
                default_description="Performance issue detected",
                default_suggestion="Review this code for performance",
            )
            if issue:
                issue["estimated_impact"] = raw_issue.get("estimated_impact") or "Unknown"
                validated_issues.append(issue)

        logger.info(f"Performance agent found {len(validated_issues)} issues in {repo_name}")
        return {"issues": validated_issues}

    except ValueError as e:
        logger.error(f"Performance agent returned invalid output: {e}")
        return {"issues": [], "_error": f"Invalid model output: {e}"}
    except Exception as e:
        logger.error(f"Performance agent failed: {e}")
        return {"issues": [], "_error": str(e)}
