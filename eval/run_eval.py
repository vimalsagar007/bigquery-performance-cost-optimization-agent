import json
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analyzers.sql_analyzer import analyze_query


def run_evaluation():
    eval_file = os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    with open(eval_file, "r") as f:
        cases = json.load(f)

    total_cases = len(cases)
    passed_cases = 0

    print("=" * 70)
    print(f"RUNNING BIGQUERY AGENT EVALUATION ({total_cases} TEST CASES)")
    print("=" * 70)

    # Mock table metadata for partitioned/clustered test cases
    mock_partitioned_meta = [{
        "full_table_id": "dataset.partitioned_table",
        "table_id": "partitioned_table",
        "partition_column": "created_date",
        "partitioning_type": "DAY"
    }]
    mock_clustered_meta = [{
        "full_table_id": "dataset.clustered_table",
        "table_id": "clustered_table",
        "clustering_fields": ["user_id", "status"]
    }]

    for case in cases:
        case_id = case["id"]
        sql = case["sql"]
        expected_rule = case["expected_rule_id"]

        meta = None
        if "partitioned_table" in sql:
            meta = mock_partitioned_meta
        elif "clustered_table" in sql:
            meta = mock_clustered_meta

        findings = analyze_query(sql, meta)
        rule_ids = [f.rule_id for f in findings]

        if expected_rule == "NONE":
            success = len(findings) == 0
        else:
            success = expected_rule in rule_ids

        if success:
            passed_cases += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"Case {case_id:2d} | [{status}] Expected: {expected_rule:32s} | Found: {rule_ids}")

    print("=" * 70)
    acc = (passed_cases / total_cases) * 100.0
    print(f"EVALUATION SUMMARY: {passed_cases}/{total_cases} PASSED ({acc:.1f}% Accuracy)")
    print("=" * 70)

    return 0 if passed_cases == total_cases else 1


if __name__ == "__main__":
    sys.exit(run_evaluation())
