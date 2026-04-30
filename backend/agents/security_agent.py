"""
Security Auditor Agent.
Analyzes code diffs for security vulnerabilities including SQL injection,
hardcoded secrets, XSS, insecure dependencies, and exposed credentials.
"""

import json
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import get_settings

logger = logging.getLogger("ai_code_review.agents.security")

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SECURITY_SYSTEM_PROMPT = """You are an expert Security Auditor AI Agent specializing in code review.
Your task is to analyze code diffs from Pull Requests and identify security vulnerabilities.

## Your Focus Areas
1. **SQL Injection** — Unsanitized user inputs in database queries, raw SQL concatenation
2. **Hardcoded Secrets** — API keys, passwords, tokens, connection strings embedded in code
3. **Exposed Credentials** — AWS keys, database passwords, private keys in source code
4. **Insecure Dependencies** — Known vulnerable library versions, deprecated security functions
5. **XSS Vulnerabilities** — Unescaped user input in HTML/templates, innerHTML usage
6. **Authentication Issues** — Missing auth checks, weak password handling, session fixation
7. **Path Traversal** — Unsanitized file paths from user input
8. **Insecure Deserialization** — Pickle/eval on untrusted data

## Output Format
You MUST return ONLY valid JSON. No markdown formatting, no code fences, no explanations outside JSON.

Return this exact JSON structure:
{
    "issues": [
        {
            "severity": "critical|high|medium|low",
            "description": "Clear description of the security issue found",
            "line_number": 42,
            "file_path": "path/to/file.py",
            "suggestion": "Specific actionable fix recommendation"
        }
    ]
}

## Severity Guidelines
- **critical**: Actively exploitable vulnerability (SQL injection, RCE, exposed production credentials)
- **high**: Serious vulnerability requiring immediate attention (XSS, hardcoded API keys, auth bypass)
- **medium**: Potential vulnerability that could be exploited under certain conditions
- **low**: Minor security concern or best practice violation

## Few-Shot Examples

### Example Input:
```diff
+ password = "admin123"
+ conn = psycopg2.connect(f"postgresql://admin:{password}@prod-db:5432/myapp")
+ query = f"SELECT * FROM users WHERE id = {user_input}"
```

### Example Output:
{
    "issues": [
        {
            "severity": "critical",
            "description": "Hardcoded database password 'admin123' found in source code. This exposes production credentials.",
            "line_number": 1,
            "file_path": null,
            "suggestion": "Move credentials to environment variables. Use: password = os.environ['DB_PASSWORD']"
        },
        {
            "severity": "critical",
            "description": "SQL injection vulnerability. User input is directly interpolated into SQL query using f-string.",
            "line_number": 3,
            "file_path": null,
            "suggestion": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_input,))"
        }
    ]
}

### Example Input (Clean Code):
```diff
+ password = os.environ.get("DB_PASSWORD")
+ cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Example Output:
{
    "issues": []
}

## Rules
- Only report issues you are confident about — no speculation
- Be specific about line numbers when possible
- Always provide actionable suggestions
- If no security issues are found, return {"issues": []}
- Return ONLY the JSON object, nothing else
"""


# ---------------------------------------------------------------------------
# Agent Function
# ---------------------------------------------------------------------------

async def run_security_agent(code_diff: str, pr_title: str, repo_name: str) -> dict[str, Any]:
    """
    Run the Security Auditor agent on a code diff.
    Returns a dict with 'issues' list containing security findings.
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
            SystemMessage(content=SECURITY_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"## Pull Request\n"
                f"**Title:** {pr_title}\n"
                f"**Repository:** {repo_name}\n\n"
                f"## Code Diff to Analyze\n"
                f"```diff\n{code_diff}\n```\n\n"
                f"Analyze this code diff for security vulnerabilities. "
                f"Return ONLY valid JSON."
            )),
        ]

        response = await llm.ainvoke(messages)
        raw_content = response.content.strip()

        # Strip markdown code fences if the model wraps the output
        if raw_content.startswith("```"):
            raw_content = raw_content.split("\n", 1)[1]  # Remove first line
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3].strip()

        result = json.loads(raw_content)

        # Validate structure
        if "issues" not in result:
            result = {"issues": []}

        # Validate each issue has required fields
        validated_issues = []
        for issue in result["issues"]:
            validated_issues.append({
                "severity": issue.get("severity", "medium"),
                "description": issue.get("description", "Security issue detected"),
                "line_number": issue.get("line_number"),
                "file_path": issue.get("file_path"),
                "suggestion": issue.get("suggestion", "Review this code for security concerns"),
            })

        logger.info(f"Security agent found {len(validated_issues)} issues in {repo_name}")
        return {"issues": validated_issues}

    except json.JSONDecodeError as e:
        logger.error(f"Security agent returned invalid JSON: {e}")
        return {"issues": [], "_error": f"JSON parse error: {str(e)}"}
    except Exception as e:
        logger.error(f"Security agent failed: {e}")
        return {"issues": [], "_error": str(e)}
