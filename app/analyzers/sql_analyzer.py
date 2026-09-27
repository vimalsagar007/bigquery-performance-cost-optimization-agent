import re
from typing import List, Dict, Any, Optional, Set
import sqlglot
import sqlglot.expressions as exp
from app.models.findings import (
    FindingItem, CategoryEnum, SeverityEnum, ConfidenceEnum
)


def extract_referenced_table_names(sql: str) -> List[str]:
    """Extracts fully qualified or dataset.table names referenced in SQL query."""
    tables: Set[str] = set()
    try:
        parsed = sqlglot.parse(sql, read="bigquery")
        for expr in parsed:
            if not expr:
                continue
            for table in expr.find_all(exp.Table):
                parts = []
                if table.catalog:
                    parts.append(table.catalog)
                if table.db:
                    parts.append(table.db)
                if table.name:
                    parts.append(table.name)
                if parts:
                    tables.add(".".join(parts))
    except Exception:
        pattern = r'`([a-zA-Z0-9_\-\.]+)`|FROM\s+([a-zA-Z0-9_\-\.]+)|JOIN\s+([a-zA-Z0-9_\-\.]+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        for match in matches:
            for group in match:
                if group and not group.upper() in {"SELECT", "WHERE", "GROUP", "ORDER", "BY"}:
                    tables.add(group)
    return sorted(list(tables))


def detect_select_star(sql: str) -> List[FindingItem]:
    """14. detect_select_star(sql)"""
    findings: List[FindingItem] = []
    
    select_star_pattern = r'SELECT\s+(\*\s*|\b[a-zA-Z0-9_]+\.\*\s*)'
    limit_pattern = r'LIMIT\s+\d+'
    
    has_star = bool(re.search(select_star_pattern, sql, re.IGNORECASE))
    has_limit = bool(re.search(limit_pattern, sql, re.IGNORECASE))

    if has_star:
        if has_limit:
            findings.append(FindingItem(
                rule_id="RULE_002_SELECT_STAR_LIMIT",
                title="SELECT * with LIMIT anti-pattern",
                category=CategoryEnum.COST,
                severity=SeverityEnum.HIGH,
                description=(
                    "Using SELECT * with LIMIT in BigQuery still scans 100% of all columns in the table, "
                    "incurring full column read costs despite restricting row output."
                ),
                evidence="Found 'SELECT *' alongside 'LIMIT'. BigQuery is a columnar store and charges per byte scanned across all projected columns.",
            ))
        else:
            findings.append(FindingItem(
                rule_id="RULE_001_SELECT_STAR",
                title="SELECT * detected",
                category=CategoryEnum.COST,
                severity=SeverityEnum.HIGH,
                description=(
                    "SELECT * projects all columns from the target table. BigQuery is a columnar database "
                    "where costs scale directly with the bytes processed in requested columns."
                ),
                evidence="Found 'SELECT *' in query string.",
            ))
            
    return findings


def detect_cross_joins(sql: str) -> List[FindingItem]:
    """18. detect_cross_joins(sql)"""
    findings: List[FindingItem] = []
    
    if re.search(r'\bCROSS\s+JOIN\b', sql, re.IGNORECASE) or re.search(r'\bJOIN\b.*?\bON\s+(1\s*=\s*1|TRUE)\b', sql, re.IGNORECASE):
        findings.append(FindingItem(
            rule_id="RULE_010_CROSS_JOIN",
            title="CROSS JOIN / Cartesian Product detected",
            category=CategoryEnum.PERFORMANCE,
            severity=SeverityEnum.CRITICAL,
            description="CROSS JOIN or join on constant (ON 1=1) produces a Cartesian product of both tables, resulting in quadratic memory and slot consumption.",
            evidence="Found explicit 'CROSS JOIN' or dummy join predicate ('ON 1=1') in query string."
        ))

    try:
        parsed = sqlglot.parse(sql, read="bigquery")
        for expr in parsed:
            if not expr:
                continue
            for join in expr.find_all(exp.Join):
                if (join.kind and join.kind.upper() == "CROSS") or (join.on and join.on.sql().strip() in ("1 = 1", "TRUE", "true")):
                    if not any(f.rule_id == "RULE_010_CROSS_JOIN" for f in findings):
                        findings.append(FindingItem(
                            rule_id="RULE_010_CROSS_JOIN",
                            title="CROSS JOIN / Cartesian Product detected",
                            category=CategoryEnum.PERFORMANCE,
                            severity=SeverityEnum.CRITICAL,
                            description="CROSS JOIN produces a Cartesian product, leading to excessive data expansion and slot exhaustion.",
                            evidence=f"AST detected CROSS JOIN or dummy ON predicate: {join.sql()}"
                        ))
    except Exception:
        pass

    return findings


def detect_large_joins(sql: str) -> List[FindingItem]:
    """17. detect_large_joins(sql)"""
    findings: List[FindingItem] = []
    
    join_count = len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE))
    if join_count >= 3:
        findings.append(FindingItem(
            rule_id="RULE_009_LARGE_JOINS",
            title="Multiple / Large Joins detected",
            category=CategoryEnum.PERFORMANCE,
            severity=SeverityEnum.MEDIUM,
            description=f"Query contains {join_count} JOIN operations. Complex multi-table joins require significant network shuffling and slot usage.",
            evidence=f"Detected {join_count} JOIN clauses in query string."
        ))
    return findings


def detect_repeated_subqueries(sql: str) -> List[FindingItem]:
    """19. detect_repeated_subqueries(sql)"""
    findings: List[FindingItem] = []
    
    subqueries: List[str] = []
    try:
        parsed = sqlglot.parse(sql, read="bigquery")
        for expr in parsed:
            if not expr:
                continue
            for select in expr.find_all(exp.Select):
                if select != expr and not isinstance(select.parent, exp.Expression):
                    pass
                sub_sql = select.sql().strip().upper()
                if len(sub_sql) > 15:
                    subqueries.append(sub_sql)
    except Exception:
        pass

    if not subqueries:
        subqueries = [sq.strip().upper() for sq in re.findall(r'\(\s*SELECT\s+[^)]+\)', sql, re.IGNORECASE)]

    seen: Dict[str, int] = {}
    for sq in subqueries:
        seen[sq] = seen.get(sq, 0) + 1

    for sq_text, count in seen.items():
        if count > 1:
            findings.append(FindingItem(
                rule_id="RULE_013_REPEATED_SUBQUERIES",
                title="Repeated Identical Subquery detected",
                category=CategoryEnum.COST,
                severity=SeverityEnum.MEDIUM,
                description="Identical subquery is repeated multiple times. Refactor into a WITH clause (CTE) to avoid duplicate dataset scans.",
                evidence=f"Identical subquery executed {count} times: '{sq_text[:60]}...'"
            ))
            
    return findings


def detect_unnecessary_columns(sql: str) -> List[FindingItem]:
    """20. detect_unnecessary_columns(sql)"""
    findings: List[FindingItem] = []
    
    try:
        parsed = sqlglot.parse(sql, read="bigquery")
        for expr in parsed:
            if not expr:
                continue
            for select in expr.find_all(exp.Select):
                expressions = select.expressions
                if len(expressions) > 20 and not any(isinstance(e, exp.Star) for e in expressions):
                    findings.append(FindingItem(
                        rule_id="RULE_005_EXCESSIVE_COLUMNS",
                        title="Excessive Column Projection detected",
                        category=CategoryEnum.COST,
                        severity=SeverityEnum.MEDIUM,
                        description=f"Query explicitly requests {len(expressions)} columns. Evaluate if all columns are required downstream.",
                        evidence=f"Projecting {len(expressions)} columns in SELECT statement."
                    ))
    except Exception:
        pass
    return findings


def detect_non_sargable_patterns(sql: str) -> List[FindingItem]:
    """21. detect_non_sargable_patterns(sql)"""
    findings: List[FindingItem] = []
    
    patterns = [
        (r'WHERE\s+.*?\b(UPPER|LOWER|DATE|FORMAT_DATE|TIMESTAMP|CAST|EXTRACT|SUBSTR)\([a-zA-Z0-9_\.]+\)', "Function applied on column in WHERE clause prevents partition pruning and index/clustering lookup."),
        (r'WHERE\s+.*?[a-zA-Z0-9_\.]+\s*LIKE\s*\'%[^\']+\'', "Leading wildcard in LIKE clause ('%string') prevents effective string index filtering."),
    ]
    
    for pat, desc in patterns:
        match = re.search(pat, sql, re.IGNORECASE)
        if match:
            findings.append(FindingItem(
                rule_id="RULE_021_NON_SARGABLE_PATTERN",
                title="Non-Sargable Predicate in WHERE Clause",
                category=CategoryEnum.PERFORMANCE,
                severity=SeverityEnum.HIGH,
                description=desc,
                evidence=f"Matched non-sargable pattern: '{match.group(0)[:80]}'"
            ))
            
    return findings


def detect_missing_partition_filter(sql: str, table_metadata_list: List[Dict[str, Any]] = None) -> List[FindingItem]:
    """15. detect_missing_partition_filter(sql)"""
    findings: List[FindingItem] = []
    if not table_metadata_list:
        return findings

    has_where = bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))
    
    for meta in table_metadata_list:
        part_col = meta.get("partition_column")
        full_name = meta.get("full_table_id", meta.get("table_id"))
        if part_col:
            if not has_where or part_col.lower() not in sql.lower():
                findings.append(FindingItem(
                    rule_id="RULE_003_MISSING_PARTITION_FILTER",
                    title=f"Missing Partition Filter on '{full_name}'",
                    category=CategoryEnum.COST,
                    severity=SeverityEnum.CRITICAL,
                    description=f"Table '{full_name}' is partitioned on column '{part_col}', but the query does not filter on '{part_col}' in the WHERE clause, triggering a full table scan.",
                    evidence=f"Partition column '{part_col}' is absent from WHERE clause filtering.",
                    affected_tables=[full_name]
                ))
    return findings


def detect_missing_clustering_filter(sql: str, table_metadata_list: List[Dict[str, Any]] = None) -> List[FindingItem]:
    """16. detect_missing_clustering_filter(sql)"""
    findings: List[FindingItem] = []
    if not table_metadata_list:
        return findings

    has_where = bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))
    
    for meta in table_metadata_list:
        cluster_fields = meta.get("clustering_fields", [])
        full_name = meta.get("full_table_id", meta.get("table_id"))
        if cluster_fields:
            missing_fields = [f for f in cluster_fields if not has_where or f.lower() not in sql.lower()]
            if missing_fields:
                findings.append(FindingItem(
                    rule_id="RULE_004_MISSING_CLUSTERING_FILTER",
                    title=f"Missing Clustering Filter on '{full_name}'",
                    category=CategoryEnum.PERFORMANCE,
                    severity=SeverityEnum.MEDIUM,
                    description=f"Table '{full_name}' is clustered on [{', '.join(cluster_fields)}], but query filters do not leverage clustering column '{missing_fields[0]}'.",
                    evidence=f"Clustering column '{missing_fields[0]}' is not used in WHERE clause.",
                    affected_tables=[full_name]
                ))
    return findings


def detect_other_antipatterns(sql: str) -> List[FindingItem]:
    """Detects ORDER BY without LIMIT, unnecessary DISTINCT, Cartesian products."""
    findings: List[FindingItem] = []
    
    if re.search(r'\bORDER\s+BY\b', sql, re.IGNORECASE) and not re.search(r'\bLIMIT\b', sql, re.IGNORECASE):
        findings.append(FindingItem(
            rule_id="RULE_011_UNNECESSARY_ORDER_BY",
            title="ORDER BY without LIMIT in subquery or main query",
            category=CategoryEnum.PERFORMANCE,
            severity=SeverityEnum.LOW,
            description="Global sorting without LIMIT forces all rows onto a single BigQuery slot, causing unnecessary sorting overhead.",
            evidence="Found 'ORDER BY' without a 'LIMIT' constraint."
        ))

    if re.search(r'\bSELECT\s+DISTINCT\b', sql, re.IGNORECASE) and re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE):
        findings.append(FindingItem(
            rule_id="RULE_012_REDUNDANT_DISTINCT",
            title="Redundant DISTINCT with GROUP BY",
            category=CategoryEnum.PERFORMANCE,
            severity=SeverityEnum.LOW,
            description="Combining DISTINCT with GROUP BY introduces redundant shuffle and hash deduplication stages.",
            evidence="Found 'SELECT DISTINCT' combined with 'GROUP BY'."
        ))
        
    return findings


def analyze_query(sql: str, table_metadata_list: List[Dict[str, Any]] = None) -> List[FindingItem]:
    """
    13. analyze_query(sql)
    Runs all AST and regex-based SQL detectors to gather evidence-backed anti-patterns.
    """
    all_findings: List[FindingItem] = []
    all_findings.extend(detect_select_star(sql))
    all_findings.extend(detect_cross_joins(sql))
    all_findings.extend(detect_large_joins(sql))
    all_findings.extend(detect_repeated_subqueries(sql))
    all_findings.extend(detect_unnecessary_columns(sql))
    all_findings.extend(detect_non_sargable_patterns(sql))
    all_findings.extend(detect_other_antipatterns(sql))
    all_findings.extend(detect_missing_partition_filter(sql, table_metadata_list))
    all_findings.extend(detect_missing_clustering_filter(sql, table_metadata_list))
    return all_findings
