import asyncio

import httpx

from openflow.config import METABASE_PASSWORD, METABASE_URL, METABASE_USERNAME

_token: str | None = None
_token_lock: asyncio.Lock | None = None
_MAX_RETRIES = 1


def _get_token_lock() -> asyncio.Lock:
    global _token_lock
    if _token_lock is None:
        _token_lock = asyncio.Lock()
    return _token_lock


async def _get_token() -> str:
    global _token
    async with _get_token_lock():
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


async def _invalidate_token() -> None:
    global _token
    async with _get_token_lock():
        _token = None


async def metabase_get(path: str, *, _retry: int = 0) -> dict:
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f'{METABASE_URL}{path}',
            headers={'X-Metabase-Session': token},
            timeout=15,
        )
        if resp.status_code == 401 and _retry < _MAX_RETRIES:
            await _invalidate_token()
            return await metabase_get(path, _retry=_retry + 1)
        resp.raise_for_status()
        return resp.json()


async def metabase_post(path: str, body: dict, *, _retry: int = 0) -> dict:
    token = await _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f'{METABASE_URL}{path}',
            headers={'X-Metabase-Session': token},
            json=body,
            timeout=30,
        )
        if resp.status_code == 401 and _retry < _MAX_RETRIES:
            await _invalidate_token()
            return await metabase_post(path, body, _retry=_retry + 1)
        resp.raise_for_status()
        return resp.json()
