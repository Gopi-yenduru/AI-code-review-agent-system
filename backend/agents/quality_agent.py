"""
Code Quality Judge Agent.
Evaluates code quality, returning a score (0-100), issues, and highlights.
"""

import os
import json
import logging
from typing import Any

model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

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
            model=model_name,
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
        raw_content = response.content.strip()

        # Strip markdown code fences if model wraps the output
        if raw_content.startswith("```"):
            raw_content = raw_content.split("\n", 1)[1]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3].strip()

        result = json.loads(raw_content)

        # Validate structure
        score = max(0, min(100, int(result.get("score", 50))))
        issues = result.get("issues", [])
        highlights = result.get("highlights", [])

        validated_issues = []
        for issue in issues:
            validated_issues.append({
                "severity": issue.get("severity", "medium"),
                "description": issue.get("description", "Quality issue detected"),
                "line_number": issue.get("line_number"),
                "file_path": issue.get("file_path"),
                "suggestion": issue.get("suggestion", "Review this code for quality"),
            })

        logger.info(f"Quality agent scored {repo_name} at {score}/100 ({len(validated_issues)} issues)")
        return {"score": score, "issues": validated_issues, "highlights": highlights}

    except json.JSONDecodeError as e:
        logger.error(f"Quality agent returned invalid JSON: {e}")
        return {"score": 50, "issues": [], "highlights": [], "_error": str(e)}
    except Exception as e:
        logger.error(f"Quality agent failed: {e}")
        return {"score": 50, "issues": [], "highlights": [], "_error": str(e)}
