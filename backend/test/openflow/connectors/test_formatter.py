"""
Unit tests for openflow.connectors.teams.formatter.format_response

format_response(result: dict) -> str

Behaviour under test:
- result with 'error' key  -> "Sorry, I couldn't answer that: <error>"
- result with empty rows   -> "No results found."
- single row, single col   -> bare string value (no table)
- multi-row                -> markdown table (header | separator | body)
- more than 20 rows        -> body capped at 20 rows + suffix line
"""

from openflow.connectors.teams.formatter import format_response


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------


def test_error_dict_returns_sorry_message():
    # Arrange
    result = {"error": "database unavailable"}

    # Act
    text = format_response(result)

    # Assert
    assert text == "Sorry, I couldn't answer that: database unavailable"


def test_error_message_is_embedded_verbatim():
    # Arrange
    result = {"error": "timeout after 30s"}

    # Act
    text = format_response(result)

    # Assert
    assert "timeout after 30s" in text


# ---------------------------------------------------------------------------
# Empty result
# ---------------------------------------------------------------------------


def test_empty_rows_returns_no_results_found():
    # Arrange
    result = {"cols": ["id", "name"], "rows": []}

    # Act
    text = format_response(result)

    # Assert
    assert text == "No results found."


def test_missing_rows_key_returns_no_results_found():
    """result dict with no 'rows' key should behave like empty rows."""
    # Arrange
    result = {"cols": ["id"]}

    # Act
    text = format_response(result)

    # Assert
    assert text == "No results found."


# ---------------------------------------------------------------------------
# Single row, single column -> bare value
# ---------------------------------------------------------------------------


def test_single_row_single_col_returns_bare_value():
    # Arrange
    result = {"cols": ["count"], "rows": [{"count": 42}]}

    # Act
    text = format_response(result)

    # Assert
    assert text == "42"


def test_single_row_single_col_string_value():
    # Arrange
    result = {"cols": ["status"], "rows": [{"status": "active"}]}

    # Act
    text = format_response(result)

    # Assert
    assert text == "active"


def test_single_row_single_col_none_value_becomes_string():
    # Arrange
    result = {"cols": ["value"], "rows": [{"value": None}]}

    # Act
    text = format_response(result)

    # Assert
    assert text == "None"


# ---------------------------------------------------------------------------
# Multi-row / multi-column -> markdown table
# ---------------------------------------------------------------------------


def test_multi_row_returns_markdown_table():
    # Arrange
    result = {
        "cols": ["id", "name"],
        "rows": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ],
    }

    # Act
    text = format_response(result)

    # Assert
    lines = text.splitlines()
    assert lines[0] == "id | name"
    assert lines[1] == "--- | ---"
    assert lines[2] == "1 | Alice"
    assert lines[3] == "2 | Bob"


def test_single_row_multi_col_returns_markdown_table():
    """One row but multiple columns should still render a table, not a bare value."""
    # Arrange
    result = {
        "cols": ["id", "name"],
        "rows": [{"id": 1, "name": "Alice"}],
    }

    # Act
    text = format_response(result)

    # Assert
    assert "id | name" in text
    assert "--- | ---" in text
    assert "1 | Alice" in text


def test_markdown_table_missing_col_value_renders_empty_string():
    """Rows that are missing a column key should render as empty string for that cell."""
    # Arrange
    result = {
        "cols": ["id", "name"],
        "rows": [{"id": 7}],  # 'name' key absent
    }

    # Act
    text = format_response(result)

    # Assert
    assert "7 | " in text


# ---------------------------------------------------------------------------
# Truncation at 20 rows
# ---------------------------------------------------------------------------


def test_exactly_20_rows_no_suffix():
    # Arrange
    rows = [{"n": i} for i in range(20)]
    result = {"cols": ["n"], "rows": rows}

    # Act
    text = format_response(result)

    # Assert
    assert "_Showing 20 of" not in text


def test_21_rows_truncates_to_20_and_shows_suffix():
    # Arrange
    rows = [{"n": i} for i in range(21)]
    result = {"cols": ["n"], "rows": rows}

    # Act
    text = format_response(result)

    # Assert
    body_lines = text.splitlines()
    # skip header + separator; collect non-empty, non-suffix lines
    data_lines = [
        l for l in body_lines[2:]
        if l and not l.startswith("_")
    ]
    assert len(data_lines) == 20
    assert "_Showing 20 of 21 rows._" in text


def test_more_than_20_rows_suffix_contains_actual_count():
    # Arrange
    rows = [{"n": i} for i in range(35)]
    result = {"cols": ["n"], "rows": rows}

    # Act
    text = format_response(result)

    # Assert
    assert "_Showing 20 of 35 rows._" in text


def test_more_than_20_rows_body_capped_at_20():
    # Arrange
    rows = [{"val": i} for i in range(50)]
    result = {"cols": ["val"], "rows": rows}

    # Act
    text = format_response(result)

    # Assert
    lines = text.splitlines()
    # lines[0] = header, lines[1] = separator, then data rows, then blank + suffix
    data_lines = [l for l in lines[2:] if l and not l.startswith("_")]
    assert len(data_lines) == 20
