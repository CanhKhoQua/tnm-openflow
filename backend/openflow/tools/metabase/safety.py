import sqlglot


_BLOCKED = {'insert', 'update', 'delete', 'drop', 'truncate', 'alter', 'create', 'replace', 'merge'}


def is_safe_sql(sql: str) -> tuple[bool, str]:
    try:
        statements = sqlglot.parse(sql)
    except sqlglot.errors.ParseError as e:
        return False, f'SQL parse error: {e}'

    if not statements:
        return False, 'Empty SQL'

    for stmt in statements:
        kind = type(stmt).__name__.lower()
        if kind in _BLOCKED:
            return False, f'Disallowed statement type: {kind}'

    return True, ''
