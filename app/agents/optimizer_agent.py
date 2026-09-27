import logging
from typing import Dict, Any, Optional, List
from app.agents.graph import agent_graph, AgentState
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, JobSummary
from app.tools.history_tools import (
    get_expensive_queries, get_slow_queries, get_failed_queries
)
from app.services.recommendation_service import generate_optimization_report

logger = logging.getLogger("bq_agent.optimizer")


class OptimizerAgent:
    def __init__(self):
        self.graph = agent_graph

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Processes natural language chat queries and orchestrates tools/agents."""
        msg = request.message.lower()
        proj = request.project_id
        reg = request.region
        days = request.days or 7

        # 1. Handle "expensive queries" natural language intent
        if "expensive" in msg or "cost" in msg and "query" in msg:
            jobs = get_expensive_queries(proj, reg, days=days, limit=5)
            if jobs:
                lines = [
                    f"1. Job `{j.job_id}`: ${j.estimated_cost_usd:.4f} USD ({j.total_bytes_billed / (1024**3):.2f} GB billed)\n   Query: `{j.query[:80]}...`"
                    for j in jobs
                ]
                ans = f"Top {len(jobs)} most expensive queries in the last {days} days:\n\n" + "\n\n".join(lines)
            else:
                ans = f"No recent expensive queries or INFORMATION_SCHEMA access unavailable for project '{proj or 'default'}'."
            return ChatResponse(intent="expensive_queries", answer=ans, query_history=jobs)

        # 2. Handle "slow queries" / "slots" intent
        if "slow" in msg or "slot" in msg:
            jobs = get_slow_queries(proj, reg, days=days, limit=5)
            if jobs:
                lines = [
                    f"1. Job `{j.job_id}`: {j.total_slot_ms:,} slot-ms ({j.duration_seconds}s duration)\n   Query: `{j.query[:80]}...`"
                    for j in jobs
                ]
                ans = f"Top {len(jobs)} slowest queries by slot consumption in the last {days} days:\n\n" + "\n\n".join(lines)
            else:
                ans = f"No recent slow queries found or INFORMATION_SCHEMA access unavailable."
            return ChatResponse(intent="slow_queries", answer=ans, query_history=jobs)

        # 3. Handle "failed queries" intent
        if "failed" in msg or "error" in msg:
            jobs = get_failed_queries(proj, reg, days=days, limit=5)
            if jobs:
                lines = [
                    f"1. Job `{j.job_id}`: Error = {j.error_result}\n   Query: `{j.query[:80]}...`"
                    for j in jobs
                ]
                ans = f"Found {len(jobs)} failed queries in the last {days} days:\n\n" + "\n\n".join(lines)
            else:
                ans = "No recent failed queries detected."
            return ChatResponse(intent="failed_queries", answer=ans, query_history=jobs)

        # 4. Handle embedded SQL or "optimize" intent
        initial_state: AgentState = {
            "sql": request.message if ("select" in msg or "with" in msg) else None,
            "user_message": request.message,
            "project_id": proj,
            "region": reg,
            "evidence": []
        }

        final_state = self.graph.invoke(initial_state)

        report = final_state.get("report")
        answer_text = final_state.get("answer", "Analyzed request.")

        return ChatResponse(
            intent=final_state.get("intent", "general"),
            answer=answer_text,
            structured_report=report,
            evidence=final_state.get("evidence", [])
        )


optimizer_agent = OptimizerAgent()
