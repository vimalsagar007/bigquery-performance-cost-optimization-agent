from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    COST = "COST"
    PERFORMANCE = "PERFORMANCE"


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConfidenceEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationItem(BaseModel):
    category: CategoryEnum
    severity: SeverityEnum
    finding: str
    evidence: str
    recommendation: str
    optimized_sql: Optional[str] = None
    expected_impact: str
    confidence: ConfidenceEnum = ConfidenceEnum.HIGH


class FindingItem(BaseModel):
    rule_id: str
    title: str
    category: CategoryEnum
    severity: SeverityEnum
    description: str
    evidence: str
    affected_tables: List[str] = Field(default_factory=list)


class EstimatedImprovement(BaseModel):
    bytes_reduction_percent: Optional[float] = None
    cost_reduction_percent: Optional[float] = None
    slot_reduction_percent: Optional[float] = None
    execution_time_reduction_percent: Optional[float] = None


class QueryOptimizationReport(BaseModel):
    query_summary: str
    bytes_processed: int = 0
    bytes_billed: int = 0
    estimated_cost: float = 0.0
    performance_findings: List[FindingItem] = Field(default_factory=list)
    cost_findings: List[FindingItem] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    optimized_sql: Optional[str] = None
    estimated_improvement: EstimatedImprovement = Field(default_factory=EstimatedImprovement)
    confidence: ConfidenceEnum = ConfidenceEnum.HIGH
    evidence: List[str] = Field(default_factory=list)
    referenced_tables: List[str] = Field(default_factory=list)
    safety_disclaimer: str = (
        "Version 1 Read-Only: Recommendations are advisory only. "
        "Generated SQL is not automatically executed."
    )


class ComparisonMetrics(BaseModel):
    original_sql: str
    optimized_sql: str
    original_bytes_processed: int
    optimized_bytes_processed: int
    bytes_saved: int
    bytes_reduction_percent: float
    original_estimated_cost: float
    optimized_estimated_cost: float
    cost_saved: float
    cost_reduction_percent: float
    comparison_summary: str
