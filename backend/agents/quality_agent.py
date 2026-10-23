"""
Code Quality Judge Agent.
Evaluates code quality, returning a score (0-100), issues, and highlights.
"""

import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from agents.output_parsing import parse_json_object, normalize_issue
from config import get_settings

logger = logging.getLogger("ai_code_review.agents.quality")

QUALITY_SYSTEM_PROMPT = """You are an expert Code Quality Judge AI Agent.
Analyze code diffs and evaluate overall code quality.

## Focus Areas
1. Naming conventions — unclear, inconsistent names
2. SOLID principle violations — tight coupling, missing abstractions
3. Dead code — unused imports, commented-out blocks, unused variables
4. Missing error handling — bare except, swallowed exceptions
5. Overly complex functions — deep nesting, high cyclomatic complexity
6. Code duplication — repeated logic needing extraction
7. Missing documentation — no docstrings on public APIs
8. Type safety — missing type hints

## Output Format
Return ONLY valid JSON, no markdown, no code fences:
{
    "score": 75,
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "description": "Description of quality issue",
            "line_number": 10,
            "file_path": "path/to/file.py",
            "suggestion": "Improvement recommendation"
        }
    ],
    "highlights": ["Positive observation about the code"]
}

## Scoring (0-100)
- 90-100: Excellent  |  70-89: Good  |  50-69: Needs Improvement
- 30-49: Poor  |  0-29: Critical
- Deductions: critical=-15, high=-10, medium=-5, low=-2. Start from 100.

## Example Input:
```diff
+ def f(x, y):
+     try:
+         result = x + y
+     except:
+         pass
+     unused = 42
+     return result
```

## Example Output:
{
    "score": 35,
    "issues": [
        {"severity": "high", "description": "Non-descriptive function name 'f'", "line_number": 1, "file_path": null, "suggestion": "Use descriptive name like 'calculate_sum'"},
        {"severity": "critical", "description": "Bare except swallows all exceptions", "line_number": 4, "file_path": null, "suggestion": "Catch specific exceptions"},
        {"severity": "medium", "description": "Unused variable 'unused'", "line_number": 6, "file_path": null, "suggestion": "Remove or prefix with underscore"}
    ],
    "highlights": []
}

## Rules
- Always provide numeric score 0-100
- Highlight positives alongside issues
- Focus on maintainability and readability
- If no issues found, return {"score": 95, "issues": [], "highlights": [...]}
- Return ONLY the JSON object
"""


async def run_quality_agent(code_diff: str, pr_title: str, repo_name: str) -> dict[str, Any]:
    """
    Run the Code Quality Judge agent on a code diff.
    Returns a dict with 'score', 'issues' list, and 'highlights' list.
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
            SystemMessage(content=QUALITY_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"## Pull Request\n"
                f"**Title:** {pr_title}\n"
                f"**Repository:** {repo_name}\n\n"
                f"## Code Diff to Analyze\n"
                f"```diff\n{code_diff}\n```\n\n"
                f"Evaluate the code quality. Return ONLY valid JSON."
            )),
        ]

        response = await llm.ainvoke(messages)
        result = parse_json_object(response.content)

        # The score is the agent's primary output — without it the response is malformed
        try:
            score = max(0, min(100, int(float(result["score"]))))
        except (KeyError, TypeError, ValueError):
            raise ValueError("Response is missing a numeric 'score'")

        issues = result.get("issues", [])
        if not isinstance(issues, list):
            raise ValueError("Response 'issues' is not a list")

        highlights = result.get("highlights", [])
        if not isinstance(highlights, list):
            highlights = []
        highlights = [str(h) for h in highlights if h]

        validated_issues = []
        for raw_issue in issues:
            issue = normalize_issue(
                raw_issue,
                default_description="Quality issue detected",
                default_suggestion="Review this code for quality",
            )
            if issue:
                validated_issues.append(issue)

        logger.info(f"Quality agent scored {repo_name} at {score}/100 ({len(validated_issues)} issues)")
        return {"score": score, "issues": validated_issues, "highlights": highlights}

    # On failure, report no score rather than inventing one
    except ValueError as e:
        logger.error(f"Quality agent returned invalid output: {e}")
        return {"score": None, "issues": [], "highlights": [], "_error": f"Invalid model output: {e}"}
    except Exception as e:
        logger.error(f"Quality agent failed: {e}")
        return {"score": None, "issues": [], "highlights": [], "_error": str(e)}
