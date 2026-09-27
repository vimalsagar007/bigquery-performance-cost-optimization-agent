import pytest
from app.tools.sql_validator import validate_sql_safety, check_and_enforce_sql_safety, SQLSafetyError


def test_safe_select_query():
    sql = "SELECT name, state FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year >= 2000"
    is_safe, reason = validate_sql_safety(sql)
    assert is_safe is True
    assert "safe" in reason.lower()


def test_reject_insert():
    sql = "INSERT INTO `my_dataset.my_table` (id, name) VALUES (1, 'test')"
    is_safe, reason = validate_sql_safety(sql)
    assert is_safe is False
    assert "INSERT" in reason

    with pytest.raises(SQLSafetyError):
        check_and_enforce_sql_safety(sql)


def test_reject_delete():
    sql = "DELETE FROM `my_dataset.my_table` WHERE id = 1"
    is_safe, reason = validate_sql_safety(sql)
    assert is_safe is False
    assert "DELETE" in reason


def test_reject_drop():
    sql = "DROP TABLE `my_dataset.my_table`"
    is_safe, reason = validate_sql_safety(sql)
    assert is_safe is False
    assert "DROP" in reason


def test_reject_create():
    sql = "CREATE TABLE `my_dataset.new_table` AS SELECT 1 as val"
    is_safe, reason = validate_sql_safety(sql)
    assert is_safe is False
    assert "CREATE" in reason
