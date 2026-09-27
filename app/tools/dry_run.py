from typing import Optional, List
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from app.config import settings
from app.tools.bigquery_tools import get_bigquery_client
from app.tools.sql_validator import validate_sql_safety
from app.models.responses import DryRunResponse


def dry_run_query(sql: str, project_id: Optional[str] = None) -> DryRunResponse:
    """
    12. dry_run_query(sql)
    Performs a BigQuery dry run to estimate bytes processed and validate SQL syntax
    without executing the query or incurring processing charges.
    """
    is_safe, safety_reason = validate_sql_safety(sql)
    if not is_safe:
        return DryRunResponse(
            valid=False,
            estimated_bytes_processed=0,
            estimated_cost_usd=0.0,
            error_message=f"Safety Guardrail Violation: {safety_reason}"
        )

    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    client = get_bigquery_client(target_project)

    job_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
    )

    try:
        query_job = client.query(sql, job_config=job_config)
        
        bytes_processed = query_job.total_bytes_processed or 0
        price_per_tb = settings.BQ_ON_DEMAND_PRICE_PER_TB
        cost_usd = (bytes_processed / (1024.0 ** 4)) * price_per_tb

        referenced_tables: List[str] = []
        if query_job.referenced_tables:
            referenced_tables = [
                f"{t.project}.{t.dataset_id}.{t.table_id}"
                for t in query_job.referenced_tables
            ]

        schema_fields: List[str] = []
        if query_job.schema:
            schema_fields = [f.name for f in query_job.schema]

        statement_type = query_job.statement_type or "SELECT"

        return DryRunResponse(
            valid=True,
            estimated_bytes_processed=bytes_processed,
            estimated_cost_usd=round(cost_usd, 6),
            statement_type=statement_type,
            referenced_tables=referenced_tables,
            schema_fields=schema_fields,
            error_message=None
        )
    except GoogleAPIError as e:
        return DryRunResponse(
            valid=False,
            estimated_bytes_processed=0,
            estimated_cost_usd=0.0,
            error_message=f"BigQuery Dry Run Error: {str(e)}"
        )
    except Exception as e:
        return DryRunResponse(
            valid=False,
            estimated_bytes_processed=0,
            estimated_cost_usd=0.0,
            error_message=f"Unexpected Dry Run Error: {str(e)}"
        )
