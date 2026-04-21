import httpx

from openflow.config import METABASE_PASSWORD, METABASE_URL, METABASE_USERNAME

_token: str | None = None


async def _get_token() -> str:
    global _token
    if _token:
        return _token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f'{METABASE_URL}/api/session',
            json={'username': METABASE_USERNAME, 'password': METABASE_PASSWORD},
            timeout=10,
        )
        resp.raise_for_status()
        _token = resp.json()['id']
    return _token


async def metabase_get(path: str) -> dict:
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f'{METABASE_URL}{path}',
            headers={'X-Metabase-Session': token},
            timeout=15,
        )
        if resp.status_code == 401:
            global _token
            _token = None
            return await metabase_get(path)
        resp.raise_for_status()
        return resp.json()


async def metabase_post(path: str, body: dict) -> dict:
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f'{METABASE_URL}{path}',
            headers={'X-Metabase-Session': token},
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
