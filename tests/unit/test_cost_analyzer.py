from app.analyzers.cost_analyzer import estimate_query_cost


def test_estimate_query_cost_calculation():
    sql = "SELECT name, state FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2020"
    res = estimate_query_cost(sql, price_per_tb=6.25)
    assert "estimated_cost_usd" in res
    assert res["price_per_tb_usd"] == 6.25
    assert isinstance(res["estimated_cost_usd"], float)
