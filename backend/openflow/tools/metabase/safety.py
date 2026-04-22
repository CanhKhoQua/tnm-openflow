import sqlglot
import sqlglot.expressions as exp


def is_safe_sql(sql: str) -> tuple[bool, str]:
    try:
        statements = sqlglot.parse(sql, error_level=sqlglot.ErrorLevel.RAISE)
    except sqlglot.errors.ParseError as e:
        return False, f'SQL parse error: {e}'

    if not statements or len(statements) != 1:
        return False, 'Exactly one SELECT statement is required'

    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        return False, f'Only SELECT statements are allowed, got: {type(stmt).__name__}'

    _DISALLOWED = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop,
        exp.Create, exp.Command, exp.Anonymous,
    )
    for node in stmt.walk():
        if isinstance(node, _DISALLOWED):
            return False, f'Disallowed expression inside query: {type(node).__name__}'

    return True, ''
