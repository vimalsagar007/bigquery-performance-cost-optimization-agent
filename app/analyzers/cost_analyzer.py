from typing import Dict, Any, Optional
from app.config import settings
from app.tools.dry_run import dry_run_query


def analyze_bytes_processed(sql: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    22. analyze_bytes_processed(sql)
    Performs a dry run to capture estimated bytes processed and provides byte scale breakdown.
    """
    dry_run_res = dry_run_query(sql, project_id)
    bytes_proc = dry_run_res.estimated_bytes_processed
    
    mb_processed = round(bytes_proc / (1024.0 ** 2), 2)
    gb_processed = round(bytes_proc / (1024.0 ** 3), 2)
    tb_processed = round(bytes_proc / (1024.0 ** 4), 4)

    return {
        "valid": dry_run_res.valid,
        "bytes_processed": bytes_proc,
        "megabytes_processed": mb_processed,
        "gigabytes_processed": gb_processed,
        "terabytes_processed": tb_processed,
        "referenced_tables": dry_run_res.referenced_tables,
        "error_message": dry_run_res.error_message
    }


def estimate_query_cost(
    sql: str,
    project_id: Optional[str] = None,
    price_per_tb: Optional[float] = None
) -> Dict[str, Any]:
    """
    23. estimate_query_cost(sql)
    Calculates estimated query processing cost based on estimated bytes processed.
    Uses configurable rate per TiB (defaults to $6.25/TiB on-demand rate).
    """
    rate = price_per_tb or settings.BQ_ON_DEMAND_PRICE_PER_TB
    bytes_info = analyze_bytes_processed(sql, project_id)
    bytes_proc = bytes_info["bytes_processed"]
    
    tb_processed = bytes_proc / (1024.0 ** 4)
    estimated_cost = round(tb_processed * rate, 6)

    return {
        "valid": bytes_info["valid"],
        "bytes_processed": bytes_proc,
        "price_per_tb_usd": rate,
        "estimated_cost_usd": estimated_cost,
        "cost_label": "Estimated query processing cost (On-Demand)",
        "disclaimer": "This is an estimate based on bytes processed during BigQuery dry-run and may differ slightly from exact Google Cloud invoice details.",
        "error_message": bytes_info.get("error_message")
    }
