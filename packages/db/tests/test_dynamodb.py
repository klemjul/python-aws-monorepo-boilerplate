"""Tests for db.dynamodb utilities."""

import os

import pytest
from db.dynamodb import build_key, paginate_result, table_name

# ---------------------------------------------------------------------------
# table_name
# ---------------------------------------------------------------------------


def test_table_name_returns_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DYNAMODB_TABLE_USERS", "prod-users-table")
    assert table_name("users") == "prod-users-table"


def test_table_name_falls_back_to_logical_name() -> None:
    os.environ.pop("DYNAMODB_TABLE_ORDERS", None)
    assert table_name("orders") == "orders"


def test_table_name_case_insensitive_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DYNAMODB_TABLE_PRODUCTS", "my-products")
    assert table_name("products") == "my-products"


# ---------------------------------------------------------------------------
# build_key
# ---------------------------------------------------------------------------


def test_build_key_returns_dict_with_s_type() -> None:
    key = build_key("id", "abc-123")
    assert key == {"id": {"S": "abc-123"}}


def test_build_key_with_custom_partition_key() -> None:
    key = build_key("orderId", "order-999")
    assert key == {"orderId": {"S": "order-999"}}


# ---------------------------------------------------------------------------
# paginate_result
# ---------------------------------------------------------------------------


def test_paginate_result_default_limit() -> None:
    items = [{"id": str(i)} for i in range(50)]
    result = paginate_result(items)
    assert len(result["items"]) == 20
    assert result["total"] == 50
    assert result["offset"] == 0


def test_paginate_result_custom_limit_and_offset() -> None:
    items = [{"id": str(i)} for i in range(10)]
    result = paginate_result(items, limit=3, offset=2)
    assert result["items"] == [{"id": "2"}, {"id": "3"}, {"id": "4"}]
    assert result["total"] == 10


def test_paginate_result_empty_list() -> None:
    result = paginate_result([])
    assert result["items"] == []
    assert result["total"] == 0


def test_paginate_result_offset_beyond_length() -> None:
    items = [{"id": "1"}, {"id": "2"}]
    result = paginate_result(items, limit=10, offset=100)
    assert result["items"] == []
