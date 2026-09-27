from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from app.models.requests import QueryAnalysisRequest, ChatRequest
from app.models.responses import JobSummary, TableMetadataResponse
from app.models.findings import QueryOptimizationReport
from app.tools.sql_validator import validate_sql_safety
from app.tools.dry_run import dry_run_query
from app.analyzers.sql_analyzer import analyze_query, extract_referenced_table_names
from app.analyzers.cost_analyzer import estimate_query_cost
from app.analyzers.performance_analyzer import analyze_slot_usage, analyze_query_performance
from app.tools.history_tools import get_expensive_queries, get_slow_queries, get_failed_queries
from app.tools.bigquery_tools import get_table_metadata
from app.services.recommendation_service import generate_optimization_report, generate_optimized_sql, compare_original_vs_optimized
from app.services.gemini_service import gemini_service


class AgentState(TypedDict, total=False):
    sql: Optional[str]
    user_message: Optional[str]
    project_id: Optional[str]
    region: Optional[str]
    intent: str
    referenced_tables: List[str]
    table_metadata: List[Dict[str, Any]]
    history_jobs: List[JobSummary]
    dry_run_result: Dict[str, Any]
    cost_info: Dict[str, Any]
    findings: List[Any]
    optimized_sql: Optional[str]
    report: Optional[QueryOptimizationReport]
    answer: str
    evidence: List[str]


def intent_node(state: AgentState) -> AgentState:
    """Classifies user intent."""
    msg = (state.get("user_message") or "").lower()
    sql = state.get("sql") or ""

    if sql or "select" in msg or "optimize" in msg or "query" in msg:
        state["intent"] = "query_analysis"
    elif "expensive" in msg or "cost" in msg:
        state["intent"] = "cost_analysis"
    elif "slow" in msg or "slot" in msg or "performance" in msg:
        state["intent"] = "performance_analysis"
    elif "failed" in msg or "error" in msg:
        state["intent"] = "history_analysis"
    else:
        state["intent"] = "query_analysis"

    return state


def query_analyzer_node(state: AgentState) -> AgentState:
    """Parses SQL and extracts anti-patterns."""
    sql = state.get("sql")
    if not sql:
        return state
    
    ref_tables = extract_referenced_table_names(sql)
    state["referenced_tables"] = ref_tables
    return state


def metadata_analyzer_node(state: AgentState) -> AgentState:
    """Fetches table metadata for referenced tables."""
    tables = state.get("referenced_tables", [])
    proj = state.get("project_id")
    metadata_list = []
    
    for t_name in tables:
        parts = t_name.split(".")
        if len(parts) == 3:
            meta = get_table_metadata(parts[0], parts[1], parts[2])
            if "error" not in meta:
                metadata_list.append(meta)
        elif len(parts) == 2:
            meta = get_table_metadata(proj, parts[0], parts[1])
            if "error" not in meta:
                metadata_list.append(meta)

    state["table_metadata"] = metadata_list
    return state


def history_analyzer_node(state: AgentState) -> AgentState:
    """Retrieves INFORMATION_SCHEMA history based on intent."""
    intent = state.get("intent")
    proj = state.get("project_id")
    reg = state.get("region")

    if intent == "cost_analysis" or "expensive" in (state.get("user_message") or "").lower():
        jobs = get_expensive_queries(proj, reg, days=7, limit=5)
    elif intent == "performance_analysis" or "slow" in (state.get("user_message") or "").lower():
        jobs = get_slow_queries(proj, reg, days=7, limit=5)
    elif "failed" in (state.get("user_message") or "").lower():
        jobs = get_failed_queries(proj, reg, days=7, limit=5)
    else:
        jobs = []

    state["history_jobs"] = jobs
    return state


def cost_analyzer_node(state: AgentState) -> AgentState:
    """Performs dry-run and cost calculation."""
    sql = state.get("sql")
    if sql:
        c_info = estimate_query_cost(sql, state.get("project_id"))
        state["cost_info"] = c_info
    return state


def performance_analyzer_node(state: AgentState) -> AgentState:
    """Runs performance & slot analysis."""
    proj = state.get("project_id")
    reg = state.get("region")
    slot_info = analyze_slot_usage(proj, reg, days=7)
    state["evidence"] = state.get("evidence", []) + [
        f"Slot usage context: Total slot ms = {slot_info.get('aggregate_slot_ms', 0):,}"
    ]
    return state


def optimizer_node(state: AgentState) -> AgentState:
    """Generates optimized SQL and findings."""
    sql = state.get("sql")
    if sql:
        table_meta = state.get("table_metadata", [])
        findings = analyze_query(sql, table_meta)
        opt_sql = generate_optimized_sql(sql, table_meta)
        state["findings"] = findings
        state["optimized_sql"] = opt_sql
    return state


def validator_node(state: AgentState) -> AgentState:
    """Validates SQL safety for optimized SQL."""
    opt_sql = state.get("optimized_sql")
    if opt_sql:
        is_safe, reason = validate_sql_safety(opt_sql)
        if not is_safe:
            state["evidence"] = state.get("evidence", []) + [f"Optimized SQL safety warning: {reason}"]
    return state


def report_generator_node(state: AgentState) -> AgentState:
    """Generates final optimization report and answer."""
    sql = state.get("sql")
    if sql:
        report = generate_optimization_report(sql, state.get("project_id"))
        state["report"] = report
        state["answer"] = report.query_summary
    else:
        history_jobs = state.get("history_jobs", [])
        if history_jobs:
            summary_lines = [f"- Job {j.job_id}: {j.estimated_cost_usd} USD, query: {j.query[:50]}..." for j in history_jobs]
            state["answer"] = f"Top historical query details:\n" + "\n".join(summary_lines)
        else:
            state["answer"] = "Analysis completed successfully."

    return state


def build_optimization_graph() -> StateGraph:
    """Builds and compiles the LangGraph agent orchestration workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("intent", intent_node)
    workflow.add_node("query_analyzer", query_analyzer_node)
    workflow.add_node("metadata_analyzer", metadata_analyzer_node)
    workflow.add_node("history_analyzer", history_analyzer_node)
    workflow.add_node("cost_analyzer", cost_analyzer_node)
    workflow.add_node("performance_analyzer", performance_analyzer_node)
    workflow.add_node("optimizer", optimizer_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("report_generator", report_generator_node)

    workflow.set_entry_point("intent")
    
    workflow.add_edge("intent", "query_analyzer")
    workflow.add_edge("query_analyzer", "metadata_analyzer")
    workflow.add_edge("metadata_analyzer", "history_analyzer")
    workflow.add_edge("history_analyzer", "cost_analyzer")
    workflow.add_edge("cost_analyzer", "performance_analyzer")
    workflow.add_edge("performance_analyzer", "optimizer")
    workflow.add_edge("optimizer", "validator")
    workflow.add_edge("validator", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


agent_graph = build_optimization_graph()
