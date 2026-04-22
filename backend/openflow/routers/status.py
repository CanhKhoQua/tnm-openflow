from fastapi import APIRouter

from openflow.connectors import registry

router = APIRouter()


@router.get('/status')
async def connector_status() -> list[dict]:
    return [{'name': c.platform_name, 'registered': True} for c in registry.all_connectors()]
