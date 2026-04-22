"""
Integration-level unit tests for openflow.tools.metabase.executor.run_query

run_query(question: str) -> dict

Strategy:
- get_schema() is patched via monkeypatch so no real Metabase schema fetch occurs.
- _nl_to_sql() is patched directly for tests that need to control the SQL string
  returned by the LLM, avoiding a live LLM HTTP mock in those cases.
- For the full-stack happy-path test, respx intercepts both the Metabase session
  and dataset HTTP calls.
- METABASE_URL and LLM_BASE_URL are read from openflow.config at import time;
  defaults are 'http://metabase:3000' and 'http://ollama:11434/v1'.

Synthetic values used throughout:
  platform names : "teams", "slack"
  user names     : "Alice", "Bob"
  ids            : 1, 2, 99999
  token          : "fake-token"
"""
import pytest
import respx
import httpx

import openflow.tools.metabase.executor as executor_module
from openflow.tools.metabase import client as metabase_client_module
from openflow.tools.metabase.executor import run_query
from openflow import config as openflow_config


# ---------------------------------------------------------------------------
# URL constants derived from config defaults
# ---------------------------------------------------------------------------

_LLM_CHAT_URL = openflow_config.LLM_BASE_URL + "/chat/completions"
_METABASE_SESSION_URL = openflow_config.METABASE_URL + "/api/session"
_METABASE_DATASET_URL = openflow_config.METABASE_URL + "/api/dataset"

_FAKE_SCHEMA = "Table: users\n  - id\n  - name"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _metabase_dataset_response(cols: list[str], rows: list[list]) -> dict:
    """Build a minimal Metabase /api/dataset response body."""
    return {
        "data": {
            "cols": [{"name": c} for c in cols],
            "rows": rows,
        }
    }


# ---------------------------------------------------------------------------
# Autouse fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_get_schema(monkeypatch: pytest.MonkeyPatch):
    """Prevent real HTTP calls to Metabase for schema fetching."""
    async def _fake_get_schema() -> str:
        return _FAKE_SCHEMA

    monkeypatch.setattr(executor_module, "get_schema", _fake_get_schema)


@pytest.fixture(autouse=True)
def _reset_metabase_token(monkeypatch: pytest.MonkeyPatch):
    """Reset the cached Metabase session token before every test."""
    monkeypatch.setattr(metabase_client_module, "_token", None)


# ---------------------------------------------------------------------------
# Test: disallowed characters in question
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_question_with_disallowed_characters_returns_error():
    # Arrange — '<' is not in [\w\s\.,\?\!\-\(\)\'\"]+
    question = "SELECT * FROM users WHERE name = <script>"

    # Act
    result = await run_query(question)

    # Assert
    assert "error" in result
    assert result["error"] == "Question contains disallowed characters"


@pytest.mark.asyncio
async def test_question_with_semicolon_returns_error():
    # Arrange — ';' is not in the safe character set
    question = "show me users; DROP TABLE users"

    # Act
    result = await run_query(question)

    # Assert
    assert "error" in result
    assert result["error"] == "Question contains disallowed characters"


@pytest.mark.asyncio
async def test_question_with_backtick_returns_error():
    # Arrange — '`' is not in the safe character set
    question = "show `users`"

    # Act
    result = await run_query(question)

    # Assert
    assert "error" in result
    assert result["error"] == "Question contains disallowed characters"


# ---------------------------------------------------------------------------
# Test: question too long is truncated, not errored
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_question_too_long_is_truncated_not_errored(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    A question longer than 500 chars that is safe after truncation must NOT
    return a sanitization error — run_query must proceed past _sanitize_question.
    We patch _nl_to_sql to capture what cleaned question was forwarded.
    """
    # Arrange — repeat a safe phrase to exceed 500 chars; all chars are in safe set
    long_question = "how many users are there " * 24  # ~600 chars, entirely safe

    captured: list[str] = []

    async def _capture_nl_to_sql(question: str, schema: str) -> str:
        captured.append(question)
        return "SELECT COUNT(*) FROM users"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _capture_nl_to_sql)

    with respx.mock(assert_all_called=False) as mock:
        mock.post(_METABASE_SESSION_URL).mock(
            return_value=httpx.Response(200, json={"id": "fake-token"})
        )
        mock.post(_METABASE_DATASET_URL).mock(
            return_value=httpx.Response(
                200,
                json=_metabase_dataset_response(["count"], [[1]]),
            )
        )

        # Act
        result = await run_query(long_question)

    # Assert — no sanitization error; question arrived at _nl_to_sql truncated
    assert "error" not in result
    assert len(captured) == 1
    assert len(captured[0]) <= 500


# ---------------------------------------------------------------------------
# Test: unsafe SQL from LLM returns error dict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_drop_table_sql_from_llm_returns_error(monkeypatch: pytest.MonkeyPatch):
    """LLM returns DROP TABLE — is_safe_sql rejects it."""
    # Arrange
    async def _bad_nl_to_sql(question: str, schema: str) -> str:
        return "DROP TABLE users"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _bad_nl_to_sql)

    # Act
    result = await run_query("delete all users")

    # Assert
    assert "error" in result
    assert "Generated SQL rejected" in result["error"]


@pytest.mark.asyncio
async def test_insert_sql_from_llm_returns_error(monkeypatch: pytest.MonkeyPatch):
    """LLM returns INSERT — is_safe_sql rejects it."""
    # Arrange
    async def _bad_nl_to_sql(question: str, schema: str) -> str:
        return "INSERT INTO users (name) VALUES ('hacked')"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _bad_nl_to_sql)

    # Act
    result = await run_query("add a user")

    # Assert
    assert "error" in result
    assert "Generated SQL rejected" in result["error"]


# ---------------------------------------------------------------------------
# Test: successful query returns cols + rows dict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_query_returns_cols_and_rows(monkeypatch: pytest.MonkeyPatch):
    # Arrange
    async def _good_nl_to_sql(question: str, schema: str) -> str:
        return "SELECT id, name FROM users"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _good_nl_to_sql)

    with respx.mock() as mock:
        mock.post(_METABASE_SESSION_URL).mock(
            return_value=httpx.Response(200, json={"id": "fake-token"})
        )
        mock.post(_METABASE_DATASET_URL).mock(
            return_value=httpx.Response(
                200,
                json=_metabase_dataset_response(
                    ["id", "name"],
                    [[1, "Alice"], [2, "Bob"]],
                ),
            )
        )

        # Act
        result = await run_query("show me all users")

    # Assert
    assert "error" not in result
    assert result["cols"] == ["id", "name"]
    assert result["rows"] == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


@pytest.mark.asyncio
async def test_successful_query_empty_result_set(monkeypatch: pytest.MonkeyPatch):
    # Arrange
    async def _good_nl_to_sql(question: str, schema: str) -> str:
        return "SELECT id FROM users WHERE id = 99999"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _good_nl_to_sql)

    with respx.mock() as mock:
        mock.post(_METABASE_SESSION_URL).mock(
            return_value=httpx.Response(200, json={"id": "fake-token"})
        )
        mock.post(_METABASE_DATASET_URL).mock(
            return_value=httpx.Response(
                200,
                json=_metabase_dataset_response(["id"], []),
            )
        )

        # Act
        result = await run_query("find user 99999")

    # Assert
    assert "error" not in result
    assert result["cols"] == ["id"]
    assert result["rows"] == []


# ---------------------------------------------------------------------------
# Test: any unexpected exception falls back to generic error dict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exception_in_nl_to_sql_returns_generic_error(
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    async def _exploding_nl_to_sql(question: str, schema: str) -> str:
        raise RuntimeError("LLM service crashed")

    monkeypatch.setattr(executor_module, "_nl_to_sql", _exploding_nl_to_sql)

    # Act
    result = await run_query("how many orders today")

    # Assert
    assert result == {"error": "An internal error occurred. Please try again."}


@pytest.mark.asyncio
async def test_metabase_http_500_returns_generic_error(
    monkeypatch: pytest.MonkeyPatch,
):
    # Arrange
    async def _good_nl_to_sql(question: str, schema: str) -> str:
        return "SELECT COUNT(*) FROM orders"

    monkeypatch.setattr(executor_module, "_nl_to_sql", _good_nl_to_sql)

    with respx.mock() as mock:
        mock.post(_METABASE_SESSION_URL).mock(
            return_value=httpx.Response(200, json={"id": "fake-token"})
        )
        mock.post(_METABASE_DATASET_URL).mock(
            return_value=httpx.Response(500)
        )

        # Act
        result = await run_query("count all orders")

    # Assert
    assert result == {"error": "An internal error occurred. Please try again."}
