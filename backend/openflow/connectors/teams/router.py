from fastapi import APIRouter, Request, Response

from openflow.connectors import registry

router = APIRouter()


@router.post('/teams/messages')
async def teams_webhook(request: Request) -> Response:
    connector = registry.get('teams')
    if connector is None:
        return Response(content='Teams connector not registered', status_code=503)

    payload = await request.json()
    payload['_auth_header'] = request.headers.get('Authorization', '')

    await connector.handle_incoming(payload)
    return Response(status_code=200)
