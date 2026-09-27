from app.models.findings import (
    RecommendationItem, QueryOptimizationReport, CategoryEnum, SeverityEnum, ConfidenceEnum
)


def test_recommendation_item_serialization():
    item = RecommendationItem(
        category=CategoryEnum.COST,
        severity=SeverityEnum.HIGH,
        finding="SELECT * Anti-pattern",
        evidence="Found 'SELECT *' in query string.",
        recommendation="Replace with explicit column projections.",
        optimized_sql="SELECT col1, col2 FROM my_table",
        expected_impact="Reduces scan size by 75%",
        confidence=ConfidenceEnum.HIGH
    )

    data = item.model_dump()
    assert data["category"] == "COST"
    assert data["severity"] == "HIGH"
    assert data["confidence"] == "HIGH"
    assert "SELECT col1" in data["optimized_sql"]
