import re
from typing import Tuple, List, Set
import sqlglot
import sqlglot.expressions as exp


FORBIDDEN_KEYWORDS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXECUTE"
}


class SQLSafetyError(ValueError):
    """Raised when SQL violates read-only safety rules."""
    pass


def validate_sql_safety(sql: str) -> Tuple[bool, str]:
    """
    Validates that a SQL query is strictly READ-ONLY and does not contain DML or DDL operations.
    Returns (is_safe, reason).
    """
    if not sql or not sql.strip():
        return False, "SQL string is empty"

    cleaned_sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    cleaned_sql = re.sub(r'/\*.*?\*/', '', cleaned_sql, flags=re.DOTALL)
    
    tokens = [t.upper() for t in re.findall(r'\b[A-Za-z_]+\b', cleaned_sql)]
    
    for forbidden in FORBIDDEN_KEYWORDS:
        if forbidden in tokens:
            return False, f"Forbidden DML/DDL keyword detected: '{forbidden}'. Version 1 is strictly read-only."

    try:
        parsed_expressions = sqlglot.parse(cleaned_sql, read="bigquery")
        for expr in parsed_expressions:
            if expr is None:
                continue
            if isinstance(expr, (exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Drop, exp.Create, exp.Alter)):
                return False, f"Forbidden AST node detected: {expr.__class__.__name__}. Only SELECT queries are permitted."
    except Exception as e:
        pass

    return True, "SQL is safe and read-only"


def check_and_enforce_sql_safety(sql: str) -> None:
    """Raises SQLSafetyError if SQL is unsafe."""
    is_safe, reason = validate_sql_safety(sql)
    if not is_safe:
        raise SQLSafetyError(reason)
