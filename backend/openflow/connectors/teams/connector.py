import json
from typing import Any

from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity

from openflow.config import TEAMS_APP_ID, TEAMS_APP_SECRET
from openflow.connectors.base import BasePlatformConnector
from openflow.connectors.teams.pipeline import TeamsPipeline


class TeamsConnector(BasePlatformConnector):
    def __init__(self) -> None:
        settings = BotFrameworkAdapterSettings(TEAMS_APP_ID, TEAMS_APP_SECRET)
        self._adapter = BotFrameworkAdapter(settings)
        self._pipeline = TeamsPipeline()

    @property
    def platform_name(self) -> str:
        return 'teams'

    async def handle_incoming(self, body: bytes, auth_header: str) -> Any:
        activity = Activity().deserialize(json.loads(body))

        async def _turn(turn_context: TurnContext) -> None:
            await self._pipeline.process(turn_context)

        return await self._adapter.process_activity(activity, auth_header, _turn)

    async def send_message(self, conversation_id: str, text: str, **kwargs: Any) -> None:
        raise NotImplementedError(
            'Proactive messaging requires a conversation reference — use pipeline.reply() instead.'
        )
