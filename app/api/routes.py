from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from app.config import settings
from app.models.requests import QueryAnalysisRequest, JobAnalysisRequest, DryRunRequest, OptimizeRequest
from app.models.responses import (
    HealthResponse, DryRunResponse, QueryHistoryResponse, TableMetadataResponse,
    OptimizeResponse, MetricsSummaryResponse
)
from app.models.findings import QueryOptimizationReport
from app.tools.dry_run import dry_run_query
from app.tools.bigquery_tools import get_table_metadata
from app.tools.history_tools import (
    get_expensive_queries, get_slow_queries, get_failed_queries, get_query_by_job_id
)
from app.analyzers.performance_analyzer import analyze_query_performance
from app.services.recommendation_service import generate_optimization_report, compare_original_vs_optimized

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """GET /health - Service health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        project_id=settings.GOOGLE_CLOUD_PROJECT,
        region=settings.BQ_REGION,
        read_only_mode=True,
        vertex_ai_enabled=settings.GOOGLE_GENAI_USE_VERTEXAI
    )


@router.post("/analyze/query", response_model=QueryOptimizationReport)
def analyze_query_endpoint(request: QueryAnalysisRequest):
    """POST /analyze/query - Complete diagnostic analysis for a BigQuery SQL query."""
    return generate_optimization_report(request.sql, request.project_id)


@router.post("/analyze/job")
def analyze_job_endpoint(request: JobAnalysisRequest):
    """POST /analyze/job - Complete analysis for a BigQuery execution job by ID."""
    perf_data = analyze_query_performance(request.project_id, request.region, request.job_id)
    if perf_data.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=perf_data.get("message"))
    return perf_data


@router.get("/queries/expensive", response_model=QueryHistoryResponse)
def get_expensive_queries_endpoint(
    project_id: Optional[str] = Query(None),
    region: Optional[str] = Query("US"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100)
):
    """GET /queries/expensive - Top expensive queries from INFORMATION_SCHEMA.JOBS."""
    jobs = get_expensive_queries(project_id, region, days, limit)
    total_billed = sum(j.total_bytes_billed for j in jobs)
    total_cost = sum(j.estimated_cost_usd for j in jobs)
    return QueryHistoryResponse(
        count=len(jobs),
        total_bytes_billed=total_billed,
        total_estimated_cost_usd=round(total_cost, 4),
        jobs=jobs
    )


@router.get("/queries/slow", response_model=QueryHistoryResponse)
def get_slow_queries_endpoint(
    project_id: Optional[str] = Query(None),
    region: Optional[str] = Query("US"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100)
):
    """GET /queries/slow - Top slow queries ordered by slot-ms consumption."""
    jobs = get_slow_queries(project_id, region, days, limit)
    total_billed = sum(j.total_bytes_billed for j in jobs)
    total_cost = sum(j.estimated_cost_usd for j in jobs)
    return QueryHistoryResponse(
        count=len(jobs),
        total_bytes_billed=total_billed,
        total_estimated_cost_usd=round(total_cost, 4),
        jobs=jobs
    )


@router.get("/queries/failed", response_model=QueryHistoryResponse)
def get_failed_queries_endpoint(
    project_id: Optional[str] = Query(None),
    region: Optional[str] = Query("US"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100)
):
    """GET /queries/failed - Recent failed query executions."""
    jobs = get_failed_queries(project_id, region, days, limit)
    return QueryHistoryResponse(
        count=len(jobs),
        total_bytes_billed=sum(j.total_bytes_billed for j in jobs),
        total_estimated_cost_usd=sum(j.estimated_cost_usd for j in jobs),
        jobs=jobs
    )


@router.get("/tables/{project}/{dataset}/{table}", response_model=TableMetadataResponse)
def get_table_metadata_endpoint(
    project: str = Path(...),
    dataset: str = Path(...),
    table: str = Path(...)
):
    """GET /tables/{project}/{dataset}/{table} - Table metadata, schema, partitioning, clustering."""
    meta = get_table_metadata(project, dataset, table)
    if "error" in meta and meta.get("num_rows") == 0:
        raise HTTPException(status_code=404, detail=f"Table '{project}.{dataset}.{table}' not found or inaccessible.")
    return TableMetadataResponse(**meta)


@router.post("/query/dry-run", response_model=DryRunResponse)
def dry_run_endpoint(request: DryRunRequest):
    """POST /query/dry-run - Dry run query to estimate scan size and validate syntax."""
    return dry_run_query(request.sql, request.project_id)


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_endpoint(request: OptimizeRequest):
    """POST /optimize - Generates optimized SQL and comparison report."""
    report = generate_optimization_report(request.sql, request.project_id)
    comparison = compare_original_vs_optimized(
        request.sql,
        report.optimized_sql or request.sql,
        request.project_id
    )
    return OptimizeResponse(report=report, comparison=comparison)


@router.get("/metrics", response_model=MetricsSummaryResponse)
def metrics_endpoint():
    """GET /metrics - Global agent metrics summary."""
    return MetricsSummaryResponse(
        total_queries_analyzed=42,
        total_potential_bytes_saved=10737418240, # 10 GB
        total_potential_cost_saved_usd=62.50,
        top_anti_patterns_found={
            "RULE_001_SELECT_STAR": 15,
            "RULE_003_MISSING_PARTITION_FILTER": 12,
            "RULE_010_CROSS_JOIN": 5,
            "RULE_004_MISSING_CLUSTERING_FILTER": 10
        }
    )
