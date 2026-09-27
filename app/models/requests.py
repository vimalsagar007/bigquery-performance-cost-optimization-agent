from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class QueryAnalysisRequest(BaseModel):
    sql: str = Field(..., description="BigQuery SQL query string to analyze")
    project_id: Optional[str] = Field(None, description="Target Google Cloud Project ID")
    region: Optional[str] = Field("US", description="BigQuery dataset/job region")


class JobAnalysisRequest(BaseModel):
    job_id: str = Field(..., description="BigQuery job ID to analyze")
    project_id: Optional[str] = Field(None, description="Google Cloud Project ID")
    region: Optional[str] = Field("US", description="BigQuery region")


class DryRunRequest(BaseModel):
    sql: str = Field(..., description="SQL query string to dry run")
    project_id: Optional[str] = Field(None, description="Google Cloud Project ID")


class OptimizeRequest(BaseModel):
    sql: str = Field(..., description="Original SQL query string to optimize")
    project_id: Optional[str] = Field(None, description="Google Cloud Project ID")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language question or instruction")
    project_id: Optional[str] = Field(None, description="Google Cloud Project ID")
    region: Optional[str] = Field("US", description="BigQuery region")
    days: Optional[int] = Field(7, description="Number of days for history queries")
