import pytest
from app.tools.dry_run import dry_run_query
from app.services.recommendation_service import generate_optimization_report


def test_public_dataset_usa_names_dry_run():
    sql = "SELECT name, gender, year, number FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2010"
    res = dry_run_query(sql)
    assert res.valid is True
    assert res.estimated_bytes_processed > 0
    assert res.estimated_cost_usd >= 0.0


def test_public_dataset_optimization_report():
    sql = "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 5"
    report = generate_optimization_report(sql)
    assert report.bytes_processed > 0
    assert len(report.cost_findings) >= 1
    assert report.optimized_sql is not None
