from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from app.config import settings
from app.tools.bigquery_tools import get_bigquery_client
from app.models.responses import JobSummary


def _parse_job_row(row: Any, price_per_tb: float) -> JobSummary:
    bytes_billed = row.get("total_bytes_billed") or 0
    estimated_cost = (bytes_billed / (1024.0 ** 4)) * price_per_tb
    creation_time_str = str(row.get("creation_time")) if row.get("creation_time") else ""
    end_time_str = str(row.get("end_time")) if row.get("end_time") else None
    
    start_t = row.get("start_time")
    end_t = row.get("end_time")
    duration_seconds = 0.0
    if start_t and end_t:
        try:
            duration_seconds = (end_t - start_t).total_seconds()
        except Exception:
            duration_seconds = 0.0

    return JobSummary(
        job_id=str(row.get("job_id")),
        project_id=str(row.get("project_id", settings.GOOGLE_CLOUD_PROJECT)),
        user_email=row.get("user_email"),
        creation_time=creation_time_str,
        end_time=end_time_str,
        query=row.get("query"),
        total_bytes_processed=row.get("total_bytes_processed") or 0,
        total_bytes_billed=bytes_billed,
        estimated_cost_usd=round(estimated_cost, 6),
        total_slot_ms=row.get("total_slot_ms") or 0,
        duration_seconds=round(duration_seconds, 2),
        state=row.get("state") or "DONE",
        error_result=str(row.get("error_result")) if row.get("error_result") else None,
        cache_hit=bool(row.get("cache_hit", False)),
    )


def get_recent_query_history(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    days: int = 7,
    limit: int = 50
) -> List[JobSummary]:
    """7. get_recent_query_history(project_id, region, days)"""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    target_region = (region or settings.BQ_REGION).lower()
    client = get_bigquery_client(target_project)
    
    query = f"""
    SELECT
      job_id,
      project_id,
      user_email,
      creation_time,
      start_time,
      end_time,
      query,
      total_bytes_processed,
      total_bytes_billed,
      total_slot_ms,
      state,
      error_result,
      cache_hit
    FROM `region-{target_region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
      AND statement_type != 'SCRIPT'
      AND query IS NOT NULL
    ORDER BY creation_time DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days", "INT64", days),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        return [_parse_job_row(row, settings.BQ_ON_DEMAND_PRICE_PER_TB) for row in results]
    except Exception as e:
        return []


def get_expensive_queries(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    days: int = 7,
    limit: int = 10
) -> List[JobSummary]:
    """8. get_expensive_queries(project_id, region, days)"""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    target_region = (region or settings.BQ_REGION).lower()
    client = get_bigquery_client(target_project)
    
    query = f"""
    SELECT
      job_id,
      project_id,
      user_email,
      creation_time,
      start_time,
      end_time,
      query,
      total_bytes_processed,
      total_bytes_billed,
      total_slot_ms,
      state,
      error_result,
      cache_hit
    FROM `region-{target_region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
      AND statement_type != 'SCRIPT'
      AND query IS NOT NULL
    ORDER BY total_bytes_billed DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days", "INT64", days),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        return [_parse_job_row(row, settings.BQ_ON_DEMAND_PRICE_PER_TB) for row in results]
    except Exception:
        return []


def get_slow_queries(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    days: int = 7,
    limit: int = 10
) -> List[JobSummary]:
    """9. get_slow_queries(project_id, region, days)"""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    target_region = (region or settings.BQ_REGION).lower()
    client = get_bigquery_client(target_project)
    
    query = f"""
    SELECT
      job_id,
      project_id,
      user_email,
      creation_time,
      start_time,
      end_time,
      query,
      total_bytes_processed,
      total_bytes_billed,
      total_slot_ms,
      state,
      error_result,
      cache_hit
    FROM `region-{target_region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
      AND statement_type != 'SCRIPT'
      AND query IS NOT NULL
    ORDER BY total_slot_ms DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days", "INT64", days),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        return [_parse_job_row(row, settings.BQ_ON_DEMAND_PRICE_PER_TB) for row in results]
    except Exception:
        return []


def get_failed_queries(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    days: int = 7,
    limit: int = 20
) -> List[JobSummary]:
    """10. get_failed_queries(project_id, region, days)"""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    target_region = (region or settings.BQ_REGION).lower()
    client = get_bigquery_client(target_project)
    
    query = f"""
    SELECT
      job_id,
      project_id,
      user_email,
      creation_time,
      start_time,
      end_time,
      query,
      total_bytes_processed,
      total_bytes_billed,
      total_slot_ms,
      state,
      error_result,
      cache_hit
    FROM `region-{target_region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
      AND (error_result IS NOT NULL OR state = 'FAILED')
    ORDER BY creation_time DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days", "INT64", days),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )
    
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        return [_parse_job_row(row, settings.BQ_ON_DEMAND_PRICE_PER_TB) for row in results]
    except Exception:
        return []


def get_query_by_job_id(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    job_id: str = ""
) -> Optional[JobSummary]:
    """11. get_query_by_job_id(project_id, region, job_id)"""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    client = get_bigquery_client(target_project)
    
    try:
        job = client.get_job(job_id, location=region or settings.BQ_REGION)
        bytes_billed = job.total_bytes_billed or 0
        est_cost = (bytes_billed / (1024.0 ** 4)) * settings.BQ_ON_DEMAND_PRICE_PER_TB
        
        duration_sec = 0.0
        if job.started and job.ended:
            duration_sec = (job.ended - job.started).total_seconds()
            
        return JobSummary(
            job_id=job.job_id,
            project_id=job.project,
            user_email=job.user_email,
            creation_time=str(job.created),
            end_time=str(job.ended) if job.ended else None,
            query=getattr(job, "query", None),
            total_bytes_processed=job.total_bytes_processed or 0,
            total_bytes_billed=bytes_billed,
            estimated_cost_usd=round(est_cost, 6),
            total_slot_ms=job.slot_millis or 0,
            duration_seconds=round(duration_sec, 2),
            state=job.state or "DONE",
            error_result=str(job.error_result) if job.error_result else None,
            cache_hit=getattr(job, "cache_hit", False) or False,
        )
    except Exception:
        return None
