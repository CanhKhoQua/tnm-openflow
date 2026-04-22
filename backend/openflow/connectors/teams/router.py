import logging

from fastapi import APIRouter, Request, Response

from openflow.connectors import registry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/teams/messages')
async def teams_webhook(request: Request) -> Response:
    connector = registry.get('teams')
    if connector is None:
        return Response(content='Teams connector not registered', status_code=503)

    body = await request.body()
    auth_header = request.headers.get('Authorization', '')

    try:
        await connector.handle_incoming(body, auth_header)
    except Exception:
        logger.exception('teams_webhook: handle_incoming failed')
        return Response(status_code=500)

    return Response(status_code=200)
