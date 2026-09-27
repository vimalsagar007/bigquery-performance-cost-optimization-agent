from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.findings import QueryOptimizationReport, ComparisonMetrics


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    project_id: str
    region: str
    read_only_mode: bool = True
    vertex_ai_enabled: bool = True


class DryRunResponse(BaseModel):
    valid: bool
    estimated_bytes_processed: int
    estimated_cost_usd: float
    statement_type: Optional[str] = None
    referenced_tables: List[str] = Field(default_factory=list)
    schema_fields: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class JobSummary(BaseModel):
    job_id: str
    project_id: str
    user_email: Optional[str] = None
    creation_time: str
    end_time: Optional[str] = None
    query: Optional[str] = None
    total_bytes_processed: int = 0
    total_bytes_billed: int = 0
    estimated_cost_usd: float = 0.0
    total_slot_ms: int = 0
    duration_seconds: float = 0.0
    state: str
    error_result: Optional[str] = None
    cache_hit: bool = False


class QueryHistoryResponse(BaseModel):
    count: int
    total_bytes_billed: int = 0
    total_estimated_cost_usd: float = 0.0
    jobs: List[JobSummary] = Field(default_factory=list)


class TableMetadataResponse(BaseModel):
    project_id: str
    dataset_id: str
    table_id: str
    full_table_id: str
    num_rows: int = 0
    num_bytes: int = 0
    num_long_term_bytes: int = 0
    partitioning_type: Optional[str] = None
    partition_column: Optional[str] = None
    clustering_fields: List[str] = Field(default_factory=list)
    table_schema: List[Dict[str, str]] = Field(default_factory=list, alias="schema")

    model_config = {"populate_by_name": True}


class OptimizeResponse(BaseModel):
    report: QueryOptimizationReport
    comparison: ComparisonMetrics


class ChatResponse(BaseModel):
    intent: str
    answer: str
    structured_report: Optional[QueryOptimizationReport] = None
    query_history: Optional[List[JobSummary]] = None
    table_metadata: Optional[TableMetadataResponse] = None
    evidence: List[str] = Field(default_factory=list)


class MetricsSummaryResponse(BaseModel):
    total_queries_analyzed: int = 0
    total_potential_bytes_saved: int = 0
    total_potential_cost_saved_usd: float = 0.0
    top_anti_patterns_found: Dict[str, int] = Field(default_factory=dict)
