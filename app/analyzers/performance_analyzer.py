from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from app.config import settings
from app.tools.bigquery_tools import get_bigquery_client
from app.tools.history_tools import get_query_by_job_id


def analyze_slot_usage(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    24. analyze_slot_usage(project_id, region, days)
    Queries INFORMATION_SCHEMA.JOBS_BY_PROJECT to evaluate slot-ms consumption,
    slot contention, and peak slot usage across recent jobs.
    """
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    target_region = (region or settings.BQ_REGION).lower()
    client = get_bigquery_client(target_project)

    query = f"""
    SELECT
      SUM(total_slot_ms) as aggregate_slot_ms,
      AVG(total_slot_ms) as avg_slot_ms_per_job,
      MAX(total_slot_ms) as max_slot_ms_single_job,
      COUNT(1) as total_jobs_count
    FROM `region-{target_region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
      AND statement_type != 'SCRIPT'
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("days", "INT64", days)
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        rows = list(query_job.result())
        if rows:
            r = rows[0]
            return {
                "project_id": target_project,
                "region": target_region,
                "days": days,
                "aggregate_slot_ms": r.get("aggregate_slot_ms") or 0,
                "avg_slot_ms_per_job": round(r.get("avg_slot_ms_per_job") or 0.0, 2),
                "max_slot_ms_single_job": r.get("max_slot_ms_single_job") or 0,
                "total_jobs_count": r.get("total_jobs_count") or 0,
                "insights": "High max_slot_ms indicates queries with heavy data shuffling or unpartitioned joins."
            }
    except Exception as e:
        pass

    return {
        "project_id": target_project,
        "region": target_region,
        "days": days,
        "aggregate_slot_ms": 0,
        "avg_slot_ms_per_job": 0.0,
        "max_slot_ms_single_job": 0,
        "total_jobs_count": 0,
        "insights": "Insufficient evidence or metadata permissions to inspect INFORMATION_SCHEMA.JOBS."
    }


def analyze_query_performance(
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    job_id: str = ""
) -> Dict[str, Any]:
    """
    25. analyze_query_performance(project_id, region, job_id)
    Inspects execution details for a specific BigQuery job, including stage execution times,
    shuffle bytes, and slot millisecond distribution.
    """
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    job_summary = get_query_by_job_id(target_project, region, job_id)

    if not job_summary:
        return {
            "job_id": job_id,
            "status": "NOT_FOUND",
            "message": f"Job ID '{job_id}' could not be located in project {target_project}."
        }

    client = get_bigquery_client(target_project)
    try:
        job = client.get_job(job_id, location=region or settings.BQ_REGION)
        
        stages_info: List[Dict[str, Any]] = []
        if hasattr(job, "query_plan") and job.query_plan:
            for stage in job.query_plan:
                stages_info.append({
                    "name": stage.name,
                    "id": stage.id,
                    "slot_ms": stage.slot_millis,
                    "records_read": stage.records_read,
                    "records_written": stage.records_written,
                    "shuffle_output_bytes": stage.shuffle_output_bytes,
                    "completed_parallel_inputs": stage.completed_parallel_inputs
                })

        return {
            "job_id": job_id,
            "status": job_summary.state,
            "query": job_summary.query,
            "total_slot_ms": job_summary.total_slot_ms,
            "duration_seconds": job_summary.duration_seconds,
            "total_bytes_processed": job_summary.total_bytes_processed,
            "total_bytes_billed": job_summary.total_bytes_billed,
            "estimated_cost_usd": job_summary.estimated_cost_usd,
            "cache_hit": job_summary.cache_hit,
            "stages_count": len(stages_info),
            "stages": stages_info,
            "error_result": job_summary.error_result
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": job_summary.state,
            "error": str(e),
            "job_summary": job_summary.model_dump()
        }
