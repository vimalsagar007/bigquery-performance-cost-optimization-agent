import re
from typing import Dict, Any, List, Optional
from app.config import settings
from app.models.findings import (
    QueryOptimizationReport, FindingItem, RecommendationItem,
    CategoryEnum, SeverityEnum, ConfidenceEnum, EstimatedImprovement, ComparisonMetrics
)
from app.tools.sql_validator import validate_sql_safety
from app.tools.dry_run import dry_run_query
from app.analyzers.sql_analyzer import analyze_query, extract_referenced_table_names
from app.analyzers.cost_analyzer import estimate_query_cost
from app.tools.bigquery_tools import get_table_metadata
from app.services.gemini_service import gemini_service


def generate_optimized_sql(sql: str, table_metadata_list: List[Dict[str, Any]] = None) -> str:
    """
    26. generate_optimized_sql(sql)
    Generates a refactored, optimized version of the BigQuery SQL query based on rule patterns.
    """
    optimized = sql

    # 1. Refactor SELECT * to specific columns if schema is available
    if re.search(r'SELECT\s+\*', sql, re.IGNORECASE) and table_metadata_list:
        for meta in table_metadata_list:
            schema = meta.get("schema", [])
            if schema:
                cols = [f["name"] for f in schema[:10]] # limit to top 10 relevant columns if huge
                col_str = ", ".join(cols)
                optimized = re.sub(r'SELECT\s+\*', f"SELECT {col_str}", optimized, flags=re.IGNORECASE, count=1)
                break

    # 2. Add partition filter hint if partition column exists and is missing in WHERE
    if table_metadata_list:
        for meta in table_metadata_list:
            part_col = meta.get("partition_column")
            if part_col and part_col.lower() not in sql.lower():
                if re.search(r'\bWHERE\b', optimized, re.IGNORECASE):
                    optimized = re.sub(
                        r'\bWHERE\b',
                        f"WHERE {part_col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND",
                        optimized,
                        flags=re.IGNORECASE,
                        count=1
                    )
                else:
                    optimized += f"\nWHERE {part_col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"

    # 3. Clean up unnecessary ORDER BY without LIMIT
    if re.search(r'\bORDER\s+BY\b', optimized, re.IGNORECASE) and not re.search(r'\bLIMIT\b', optimized, re.IGNORECASE):
        # Only comment or add LIMIT 1000 if not top level
        pass

    return optimized.strip()


def compare_original_vs_optimized(
    original_sql: str,
    optimized_sql: str,
    project_id: Optional[str] = None
) -> ComparisonMetrics:
    """
    28. compare_original_vs_optimized(original_sql, optimized_sql)
    Performs dry-runs on both original and optimized queries to calculate
    measured / estimated byte reductions and cost savings.
    """
    orig_dry = dry_run_query(original_sql, project_id)
    opt_dry = dry_run_query(optimized_sql, project_id)

    orig_bytes = orig_dry.estimated_bytes_processed
    opt_bytes = opt_dry.estimated_bytes_processed if opt_dry.valid else orig_bytes

    bytes_saved = max(0, orig_bytes - opt_bytes)
    bytes_reduction_pct = round((bytes_saved / orig_bytes * 100.0), 2) if orig_bytes > 0 else 0.0

    orig_cost = orig_dry.estimated_cost_usd
    opt_cost = opt_dry.estimated_cost_usd if opt_dry.valid else orig_cost
    cost_saved = round(max(0.0, orig_cost - opt_cost), 6)
    cost_reduction_pct = round((cost_saved / orig_cost * 100.0), 2) if orig_cost > 0 else 0.0

    summary = (
        f"Optimized SQL reduces estimated scan volume by {bytes_reduction_pct}% "
        f"({bytes_saved} bytes) and decreases estimated query processing cost by ${cost_saved} USD."
    )

    return ComparisonMetrics(
        original_sql=original_sql,
        optimized_sql=optimized_sql,
        original_bytes_processed=orig_bytes,
        optimized_bytes_processed=opt_bytes,
        bytes_saved=bytes_saved,
        bytes_reduction_percent=bytes_reduction_pct,
        original_estimated_cost=orig_cost,
        optimized_estimated_cost=opt_cost,
        cost_saved=cost_saved,
        cost_reduction_percent=cost_reduction_pct,
        comparison_summary=summary
    )


def generate_optimization_report(
    sql: str,
    project_id: Optional[str] = None
) -> QueryOptimizationReport:
    """
    27. generate_optimization_report(sql)
    Coordinates dry-run, AST analysis, metadata retrieval, Gemini reasoning,
    and returns a full QueryOptimizationReport.
    """
    is_safe, safety_msg = validate_sql_safety(sql)
    if not is_safe:
        return QueryOptimizationReport(
            query_summary=f"Query rejected by safety guardrails: {safety_msg}",
            performance_findings=[],
            cost_findings=[],
            recommendations=[],
            safety_disclaimer=f"REJECTED: {safety_msg}"
        )

    # 1. Dry run
    dry_run_res = dry_run_query(sql, project_id)
    bytes_proc = dry_run_res.estimated_bytes_processed
    cost_usd = dry_run_res.estimated_cost_usd
    referenced_tables = dry_run_res.referenced_tables

    if not referenced_tables:
        referenced_tables = extract_referenced_table_names(sql)

    # 2. Fetch table metadata for referenced tables
    table_meta_list = []
    for t_name in referenced_tables:
        parts = t_name.split(".")
        if len(parts) == 3:
            meta = get_table_metadata(parts[0], parts[1], parts[2])
            if "error" not in meta:
                table_meta_list.append(meta)
        elif len(parts) == 2:
            proj = project_id or settings.GOOGLE_CLOUD_PROJECT
            meta = get_table_metadata(proj, parts[0], parts[1])
            if "error" not in meta:
                table_meta_list.append(meta)

    # 3. Analyze anti-patterns
    findings = analyze_query(sql, table_meta_list)
    
    cost_findings = [f for f in findings if f.category == CategoryEnum.COST]
    perf_findings = [f for f in findings if f.category == CategoryEnum.PERFORMANCE]

    # 4. Generate recommendations
    recommendations: List[RecommendationItem] = []
    for f in findings:
        opt_sql = None
        if f.rule_id == "RULE_001_SELECT_STAR":
            opt_sql = re.sub(r'SELECT\s+\*', 'SELECT col1, col2, col3', sql, flags=re.IGNORECASE, count=1)
        elif f.rule_id == "RULE_003_MISSING_PARTITION_FILTER" and f.affected_tables:
            opt_sql = f"{sql}\nWHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"

        recommendations.append(RecommendationItem(
            category=f.category,
            severity=f.severity,
            finding=f.title,
            evidence=f.evidence,
            recommendation=f.description,
            optimized_sql=opt_sql,
            expected_impact=f"Potential reduction in bytes processed or slot consumption.",
            confidence=ConfidenceEnum.HIGH
        ))

    # 5. Generate Refactored SQL
    optimized_sql = generate_optimized_sql(sql, table_meta_list)
    
    # 6. Calculate improvement estimate
    comparison = compare_original_vs_optimized(sql, optimized_sql, project_id)
    est_improvement = EstimatedImprovement(
        bytes_reduction_percent=comparison.bytes_reduction_percent,
        cost_reduction_percent=comparison.cost_reduction_percent
    )

    evidence_summary = [
        f"Dry-run estimated bytes processed: {bytes_proc:,} bytes.",
        f"Estimated processing cost: ${cost_usd:.6f} USD at ${settings.BQ_ON_DEMAND_PRICE_PER_TB}/TiB.",
        f"Referenced tables: {', '.join(referenced_tables) if referenced_tables else 'None detected'}.",
        f"Anti-patterns detected: {len(findings)}."
    ]

    summary_text = (
        f"Query scans {bytes_proc / (1024**2):.2f} MB yielding an estimated cost of ${cost_usd:.4f} USD. "
        f"Identified {len(findings)} anti-pattern(s)."
    )

    return QueryOptimizationReport(
        query_summary=summary_text,
        bytes_processed=bytes_proc,
        bytes_billed=bytes_proc,
        estimated_cost=cost_usd,
        performance_findings=perf_findings,
        cost_findings=cost_findings,
        recommendations=recommendations,
        optimized_sql=optimized_sql,
        estimated_improvement=est_improvement,
        confidence=ConfidenceEnum.HIGH if dry_run_res.valid else ConfidenceEnum.MEDIUM,
        evidence=evidence_summary,
        referenced_tables=referenced_tables
    )
