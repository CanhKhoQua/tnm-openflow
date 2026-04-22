"""
Unit tests for openflow.tools.metabase.safety.is_safe_sql

is_safe_sql(sql) -> tuple[bool, str]

Rules enforced by the implementation:
- sqlglot must parse without error
- Exactly one statement
- That statement must be exp.Select
- No disallowed expressions (Insert, Update, Delete, Drop, Create, Command, Anonymous)
  may appear anywhere inside the tree
"""

import pytest

from openflow.tools.metabase.safety import is_safe_sql


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


def test_valid_select_passes():
    # Arrange
    sql = 'SELECT id, name FROM users'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is True
    assert reason == ''


def test_select_with_where_passes():
    # Arrange
    sql = "SELECT * FROM orders WHERE status = 'active'"

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is True
    assert reason == ''


def test_select_with_subquery_passes():
    # Arrange
    sql = 'SELECT id FROM users WHERE id IN (SELECT user_id FROM orders)'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is True
    assert reason == ''


def test_select_with_join_passes():
    # Arrange
    sql = 'SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is True
    assert reason == ''


# ---------------------------------------------------------------------------
# Blocked DML / DDL statement types
# ---------------------------------------------------------------------------


def test_insert_blocked():
    # Arrange
    sql = "INSERT INTO users (name) VALUES ('bob')"

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_update_blocked():
    # Arrange
    sql = "UPDATE users SET name = 'bob' WHERE id = 1"

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_delete_blocked():
    # Arrange
    sql = 'DELETE FROM users WHERE id = 1'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_drop_table_blocked():
    # Arrange
    sql = 'DROP TABLE users'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_create_table_blocked():
    # Arrange
    sql = 'CREATE TABLE new_table (id INT)'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_execute_blocked():
    """EXECUTE is parsed as a Command by sqlglot, which is in the disallowed set."""
    # Arrange
    sql = 'EXECUTE some_proc'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


# ---------------------------------------------------------------------------
# Multi-statement tests
# ---------------------------------------------------------------------------


def test_multi_statement_select_then_drop_blocked():
    # Arrange
    sql = 'SELECT id FROM users; DROP TABLE users'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_multi_statement_two_selects_blocked():
    """Even two SELECTs are rejected — exactly one statement is required."""
    # Arrange
    sql = 'SELECT 1; SELECT 2'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert 'Exactly one SELECT statement' in reason


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_string_blocked():
    # Arrange
    sql = ''

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_whitespace_only_blocked():
    # Arrange
    sql = '   \n\t  '

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_malformed_sql_blocked():
    """Completely broken SQL that sqlglot cannot parse should return False."""
    # Arrange
    sql = 'SELECT FROM WHERE AND'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert reason != ''


def test_reason_empty_on_success():
    """The second element of the tuple MUST be an empty string on success."""
    # Arrange
    sql = 'SELECT COUNT(*) FROM orders'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is True
    assert reason == ''


def test_reason_non_empty_on_failure():
    """The second element of the tuple MUST carry a non-empty message on failure."""
    # Arrange
    sql = 'INSERT INTO t VALUES (1)'

    # Act
    ok, reason = is_safe_sql(sql)

    # Assert
    assert ok is False
    assert isinstance(reason, str)
    assert len(reason) > 0


def test_returns_tuple_of_bool_and_str():
    """Return type contract: (bool, str) for both success and failure paths."""
    for sql in ('SELECT 1', 'DROP TABLE x'):
        ok, reason = is_safe_sql(sql)
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
