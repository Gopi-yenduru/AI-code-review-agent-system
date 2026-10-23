"""
LangGraph Multi-Agent Pipeline.
Orchestrates three AI agents (Security, Performance, Quality) in parallel
using LangGraph's StateGraph with static branching and a merge node.
"""

import operator
import logging
from typing import Any, Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

from agents.security_agent import run_security_agent
from agents.performance_agent import run_performance_agent
from agents.quality_agent import run_quality_agent

logger = logging.getLogger("ai_code_review.agents.graph")


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------

def merge_dicts(left: dict, right: dict) -> dict:
    """Reducer that merges two dictionaries."""
    merged = left.copy()
    merged.update(right)
    return merged


class ReviewState(TypedDict):
    """State schema for the review pipeline."""
    # Input fields
    code_diff: str
    pr_title: str
    repo_name: str

    # Agent output fields — merged via reducer
    security: Annotated[dict, merge_dicts]
    performance: Annotated[dict, merge_dicts]
    quality: Annotated[dict, merge_dicts]

    # Final output
    overall_risk_score: float
    failed_agents: list[str]
    review_complete: bool


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------

async def security_node(state: ReviewState) -> dict[str, Any]:
    """Run the Security Auditor agent."""
    logger.info("🔒 Running Security Auditor...")
    result = await run_security_agent(
        code_diff=state["code_diff"],
        pr_title=state["pr_title"],
        repo_name=state["repo_name"],
    )
    logger.info(f"🔒 Security Auditor complete: {len(result.get('issues', []))} issues")
    return {"security": result}


async def performance_node(state: ReviewState) -> dict[str, Any]:
    """Run the Performance Analyst agent."""
    logger.info("⚡ Running Performance Analyst...")
    result = await run_performance_agent(
        code_diff=state["code_diff"],
        pr_title=state["pr_title"],
        repo_name=state["repo_name"],
    )
    logger.info(f"⚡ Performance Analyst complete: {len(result.get('issues', []))} issues")
    return {"performance": result}


async def quality_node(state: ReviewState) -> dict[str, Any]:
    """Run the Code Quality Judge agent."""
    logger.info("📋 Running Code Quality Judge...")
    result = await run_quality_agent(
        code_diff=state["code_diff"],
        pr_title=state["pr_title"],
        repo_name=state["repo_name"],
    )
    logger.info(f"📋 Code Quality Judge complete: score={result.get('score', 'N/A')}")
    return {"quality": result}


# ---------------------------------------------------------------------------
# Merge Node
# ---------------------------------------------------------------------------

# Fraction of the remaining "safe" headroom that a single issue consumes
SEVERITY_RISK = {
    "critical": 0.75,
    "high": 0.5,
    "medium": 0.25,
    "low": 0.05,
}

AGENT_NAMES = ("security", "performance", "quality")


def calculate_risk_score(
    security_issues: list[dict],
    performance_issues: list[dict],
) -> float:
    """
    Calculate overall risk score (0-100) from security and performance issues.

    Each issue removes a fraction of the remaining headroom:
        risk = 100 × (1 − ∏(1 − w_i))
    with w = critical 0.75, high 0.5, medium 0.25, low 0.05.

    The score only grows as issues are added and never exceeds 100. A single
    issue lands on its severity's band threshold: one critical → 75 (CRITICAL),
    one high → 50 (HIGH), one medium → 25 (MEDIUM), one low → 5 (LOW).
    """
    safe = 1.0
    for issue in security_issues + performance_issues:
        safe *= 1 - SEVERITY_RISK.get(issue.get("severity"), SEVERITY_RISK["medium"])
    return round((1 - safe) * 100, 1)


async def merge_node(state: ReviewState) -> dict[str, Any]:
    """Merge all agent outputs, record failed agents, and calculate the overall risk score."""
    logger.info("🔀 Merging agent results...")

    security = state.get("security", {"issues": []})
    performance = state.get("performance", {"issues": []})
    quality = state.get("quality", {"score": None, "issues": [], "highlights": []})

    security_issues = security.get("issues", [])
    performance_issues = performance.get("issues", [])

    risk_score = calculate_risk_score(security_issues, performance_issues)

    # Agents report failures via "_error" — surface them instead of treating them as clean results
    failed_agents = [name for name in AGENT_NAMES if state.get(name, {}).get("_error")]
    if failed_agents:
        logger.warning(f"⚠️ Agents failed: {', '.join(failed_agents)} — review is incomplete")

    logger.info(
        f"✅ Review complete — Risk Score: {risk_score}/100 | "
        f"Security: {len(security_issues)} issues | "
        f"Performance: {len(performance_issues)} issues | "
        f"Quality: {quality.get('score') if quality.get('score') is not None else 'N/A'}/100"
    )

    return {
        "overall_risk_score": risk_score,
        "failed_agents": failed_agents,
        "review_complete": True,
    }


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_review_graph() -> StateGraph:
    """
    Build the LangGraph pipeline with parallel agent execution.

    Flow:
        START ──┬── security_node ──┐
                ├── performance_node ├── merge_node ── END
                └── quality_node ───┘
    """
    graph = StateGraph(ReviewState)

    # Add nodes
    graph.add_node("security_node", security_node)
    graph.add_node("performance_node", performance_node)
    graph.add_node("quality_node", quality_node)
    graph.add_node("merge_node", merge_node)

    # Parallel fan-out from START to all 3 agents
    graph.add_edge(START, "security_node")
    graph.add_edge(START, "performance_node")
    graph.add_edge(START, "quality_node")

    # Fan-in from all 3 agents to merge node
    graph.add_edge("security_node", "merge_node")
    graph.add_edge("performance_node", "merge_node")
    graph.add_edge("quality_node", "merge_node")

    # Merge node to END
    graph.add_edge("merge_node", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Pre-compiled graph instance
review_graph = build_review_graph()


async def run_review_pipeline(
    code_diff: str,
    pr_title: str,
    repo_name: str,
) -> dict[str, Any]:
    """
    Execute the full multi-agent review pipeline.
    Returns the final state with all agent results and risk score.
    """
    logger.info(f"🚀 Starting review pipeline for {repo_name}: {pr_title}")

    initial_state: ReviewState = {
        "code_diff": code_diff,
        "pr_title": pr_title,
        "repo_name": repo_name,
        "security": {},
        "performance": {},
        "quality": {},
        "overall_risk_score": 0.0,
        "failed_agents": [],
        "review_complete": False,
    }

    result = await review_graph.ainvoke(initial_state)

    return {
        "security": result.get("security", {}),
        "performance": result.get("performance", {}),
        "quality": result.get("quality", {}),
        "overall_risk_score": result.get("overall_risk_score", 0.0),
        "failed_agents": result.get("failed_agents", []),
    }
