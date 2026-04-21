from typing import Any


def format_response(result: dict[str, Any]) -> str:
    if 'error' in result:
        return f"Sorry, I couldn't answer that: {result['error']}"

    rows: list[dict] = result.get('rows', [])
    cols: list[str] = result.get('cols', [])

    if not rows:
        return 'No results found.'

    if len(rows) == 1 and len(cols) == 1:
        return str(rows[0][cols[0]])

    header = ' | '.join(cols)
    separator = ' | '.join(['---'] * len(cols))
    body = '\n'.join(' | '.join(str(row.get(c, '')) for c in cols) for row in rows[:20])

    suffix = f'\n\n_Showing 20 of {len(rows)} rows._' if len(rows) > 20 else ''
    return f'{header}\n{separator}\n{body}{suffix}'
