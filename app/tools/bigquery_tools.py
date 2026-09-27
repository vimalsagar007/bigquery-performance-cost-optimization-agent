from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from app.config import settings


def get_bigquery_client(project_id: Optional[str] = None) -> bigquery.Client:
    """Returns an authenticated BigQuery Client using Application Default Credentials."""
    target_project = project_id or settings.GOOGLE_CLOUD_PROJECT
    return bigquery.Client(project=target_project)


def list_datasets(project_id: Optional[str] = None) -> List[str]:
    """1. list_datasets(project_id)"""
    client = get_bigquery_client(project_id)
    datasets = list(client.list_datasets(project=project_id or settings.GOOGLE_CLOUD_PROJECT))
    return [ds.dataset_id for ds in datasets]


def list_tables(project_id: Optional[str] = None, dataset_id: str = "") -> List[str]:
    """2. list_tables(project_id, dataset_id)"""
    client = get_bigquery_client(project_id)
    dataset_ref = bigquery.DatasetReference(project_id or settings.GOOGLE_CLOUD_PROJECT, dataset_id)
    tables = list(client.list_tables(dataset_ref))
    return [t.table_id for t in tables]


def get_table_metadata(project_id: str, dataset_id: str, table_id: str) -> Dict[str, Any]:
    """3. get_table_metadata(project_id, dataset_id, table_id)"""
    client = get_bigquery_client(project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    try:
        table = client.get_table(table_ref)
        
        partition_col = None
        partition_type = None
        if table.time_partitioning:
            partition_type = table.time_partitioning.type_
            partition_col = table.time_partitioning.field or "_PARTITIONDATE"
        elif table.range_partitioning:
            partition_type = "RANGE"
            partition_col = table.range_partitioning.field

        clustering_fields = list(table.clustering_fields) if table.clustering_fields else []

        schema_list = [
            {
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
                "description": field.description or ""
            }
            for field in table.schema
        ]

        num_bytes = getattr(table, "num_bytes", 0) or 0
        num_rows = getattr(table, "num_rows", 0) or 0
        long_term_bytes = getattr(table, "num_long_term_bytes", 0) or 0

        return {
            "project_id": table.project,
            "dataset_id": table.dataset_id,
            "table_id": table.table_id,
            "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
            "num_rows": num_rows,
            "num_bytes": num_bytes,
            "num_long_term_bytes": long_term_bytes,
            "partitioning_type": partition_type,
            "partition_column": partition_col,
            "clustering_fields": clustering_fields,
            "schema": schema_list,
        }
    except GoogleAPIError as e:
        return {
            "project_id": project_id,
            "dataset_id": dataset_id,
            "table_id": table_id,
            "full_table_id": f"{project_id}.{dataset_id}.{table_id}",
            "error": str(e),
            "num_rows": 0,
            "num_bytes": 0,
            "num_long_term_bytes": 0,
            "partitioning_type": None,
            "partition_column": None,
            "clustering_fields": [],
            "schema": []
        }


def get_table_schema(project_id: str, dataset_id: str, table_id: str) -> List[Dict[str, str]]:
    """4. get_table_schema(project_id, dataset_id, table_id)"""
    meta = get_table_metadata(project_id, dataset_id, table_id)
    return meta.get("schema", [])


def get_partitioning_info(project_id: str, dataset_id: str, table_id: str) -> Dict[str, Any]:
    """5. get_partitioning_info(project_id, dataset_id, table_id)"""
    meta = get_table_metadata(project_id, dataset_id, table_id)
    return {
        "is_partitioned": meta.get("partitioning_type") is not None,
        "partitioning_type": meta.get("partitioning_type"),
        "partition_column": meta.get("partition_column")
    }


def get_clustering_info(project_id: str, dataset_id: str, table_id: str) -> Dict[str, Any]:
    """6. get_clustering_info(project_id, dataset_id, table_id)"""
    meta = get_table_metadata(project_id, dataset_id, table_id)
    fields = meta.get("clustering_fields", [])
    return {
        "is_clustered": len(fields) > 0,
        "clustering_fields": fields
    }
