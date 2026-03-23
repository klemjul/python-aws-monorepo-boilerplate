"""DynamoDB helper utilities."""

import os
from typing import Any


def table_name(logical_name: str) -> str:
    """Return the DynamoDB table name for a given logical name.

    Reads the ``DYNAMODB_TABLE_{LOGICAL_NAME_UPPER}`` environment variable.
    Falls back to the logical name itself when the variable is not set.

    Args:
        logical_name: The short name of the table (e.g. ``"users"``).

    Returns:
        The resolved DynamoDB table name string.
    """
    env_key = f"DYNAMODB_TABLE_{logical_name.upper()}"
    return os.environ.get(env_key, logical_name)


def build_key(partition_key: str, partition_value: str) -> dict[str, Any]:
    """Build a DynamoDB key dict for a single-key table.

    Args:
        partition_key: The name of the partition key attribute.
        partition_value: The value of the partition key.

    Returns:
        A dict suitable for use as a DynamoDB ``Key`` argument.
    """
    return {partition_key: {"S": partition_value}}


def paginate_result(
    items: list[dict[str, Any]],
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Return a paginated slice of items with metadata.

    Args:
        items: The full list of items to paginate.
        limit: Maximum number of items to return.
        offset: Zero-based starting index.

    Returns:
        A dict with ``items``, ``total``, ``limit``, and ``offset`` fields.
    """
    sliced = items[offset : offset + limit]
    return {
        "items": sliced,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }
