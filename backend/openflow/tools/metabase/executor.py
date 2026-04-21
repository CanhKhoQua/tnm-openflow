from openflow.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, METABASE_DATABASE_ID
from openflow.tools.metabase.client import metabase_post
from openflow.tools.metabase.safety import is_safe_sql
from openflow.tools.metabase.schema import get_schema

import httpx


async def _nl_to_sql(question: str, schema: str) -> str:
    prompt = (
        f'You are a SQL expert. Given this database schema:\n\n{schema}\n\n'
        f'Write a single read-only SQL SELECT query to answer: {question}\n\n'
        f'Return only the SQL, no explanation.'
    )
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f'{LLM_BASE_URL}/chat/completions',
            headers={'Authorization': f'Bearer {LLM_API_KEY}'} if LLM_API_KEY else {},
            json={
                'model': LLM_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content'].strip()


async def run_query(question: str) -> dict:
    try:
        schema = await get_schema()
        sql = await _nl_to_sql(question, schema)

        safe, reason = is_safe_sql(sql)
        if not safe:
            return {'error': f'Generated SQL rejected: {reason}'}

        result = await metabase_post(
            '/api/dataset',
            {'database': METABASE_DATABASE_ID, 'type': 'native', 'native': {'query': sql}},
        )

        data = result.get('data', {})
        cols = [c['name'] for c in data.get('cols', [])]
        rows = [dict(zip(cols, row)) for row in data.get('rows', [])]
        return {'cols': cols, 'rows': rows}

    except Exception as e:
        return {'error': str(e)}
