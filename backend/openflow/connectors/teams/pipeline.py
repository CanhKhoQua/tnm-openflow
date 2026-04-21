from botbuilder.core import TurnContext

from openflow.connectors.teams.formatter import format_response
from openflow.tools.metabase.executor import run_query


class TeamsPipeline:
    async def process(self, turn_context: TurnContext) -> None:
        user_text = (turn_context.activity.text or '').strip()
        if not user_text:
            return

        result = await run_query(user_text)
        reply_text = format_response(result)
        await turn_context.send_activity(reply_text)
