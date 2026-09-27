from app.analyzers.sql_analyzer import (
    detect_select_star, detect_cross_joins, detect_large_joins,
    detect_repeated_subqueries, detect_non_sargable_patterns, analyze_query
)


def test_detect_select_star():
    sql = "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current`"
    findings = detect_select_star(sql)
    assert len(findings) == 1
    assert findings[0].rule_id == "RULE_001_SELECT_STAR"


def test_detect_select_star_limit():
    sql = "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 10"
    findings = detect_select_star(sql)
    assert len(findings) == 1
    assert findings[0].rule_id == "RULE_002_SELECT_STAR_LIMIT"


def test_detect_cross_join():
    sql = "SELECT a.name, b.name FROM table1 a CROSS JOIN table2 b"
    findings = detect_cross_joins(sql)
    assert len(findings) >= 1
    assert findings[0].rule_id == "RULE_010_CROSS_JOIN"


def test_detect_large_joins():
    sql = "SELECT * FROM t1 JOIN t2 ON t1.id=t2.id JOIN t3 ON t2.id=t3.id JOIN t4 ON t3.id=t4.id"
    findings = detect_large_joins(sql)
    assert len(findings) == 1
    assert findings[0].rule_id == "RULE_009_LARGE_JOINS"


def test_detect_non_sargable_predicate():
    sql = "SELECT name FROM my_table WHERE UPPER(name) = 'ALICE'"
    findings = detect_non_sargable_patterns(sql)
    assert len(findings) == 1
    assert findings[0].rule_id == "RULE_021_NON_SARGABLE_PATTERN"
