import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from open_webui.config import CONFIG_DATA, async_save_config
from open_webui.utils.auth import get_admin_user

import openflow.config as openflow_config

logger = logging.getLogger(__name__)
router = APIRouter()


class OpenflowSettings(BaseModel):
    teams_app_id: str = ''
    teams_app_secret: str = ''
    teams_tenant_id: str = ''
    metabase_url: str = ''
    metabase_username: str = ''
    metabase_password: str = ''
    metabase_database_id: int = 1
    schema_cache_minutes: int = 60
    llm_base_url: str = ''
    llm_model: str = ''
    llm_api_key: str = ''


class OpenflowSettingsResponse(BaseModel):
    teams_app_id: str
    teams_app_secret_set: bool
    teams_tenant_id: str
    metabase_url: str
    metabase_username: str
    metabase_password_set: bool
    metabase_database_id: int
    schema_cache_minutes: int
    llm_base_url: str
    llm_model: str
    llm_api_key_set: bool


def _current_settings() -> OpenflowSettingsResponse:
    return OpenflowSettingsResponse(
        teams_app_id=openflow_config.TEAMS_APP_ID.value,
        teams_app_secret_set=bool(openflow_config.TEAMS_APP_SECRET.value),
        teams_tenant_id=openflow_config.TEAMS_TENANT_ID.value,
        metabase_url=openflow_config.METABASE_URL.value,
        metabase_username=openflow_config.METABASE_USERNAME.value,
        metabase_password_set=bool(openflow_config.METABASE_PASSWORD.value),
        metabase_database_id=openflow_config.METABASE_DATABASE_ID.value,
        schema_cache_minutes=openflow_config.SCHEMA_CACHE_MINUTES.value,
        llm_base_url=openflow_config.LLM_BASE_URL.value,
        llm_model=openflow_config.LLM_MODEL.value,
        llm_api_key_set=bool(openflow_config.LLM_API_KEY.value),
    )


@router.get('/settings', response_model=OpenflowSettingsResponse)
async def get_settings(user=Depends(get_admin_user)):
    return _current_settings()


@router.post('/settings', response_model=OpenflowSettingsResponse)
async def update_settings(body: OpenflowSettings, user=Depends(get_admin_user)):
    openflow_config.TEAMS_APP_ID.value = body.teams_app_id
    openflow_config.TEAMS_TENANT_ID.value = body.teams_tenant_id
    openflow_config.METABASE_URL.value = body.metabase_url
    openflow_config.METABASE_USERNAME.value = body.metabase_username
    openflow_config.METABASE_DATABASE_ID.value = body.metabase_database_id
    openflow_config.SCHEMA_CACHE_MINUTES.value = body.schema_cache_minutes
    openflow_config.LLM_BASE_URL.value = body.llm_base_url
    openflow_config.LLM_MODEL.value = body.llm_model

    # Only overwrite secrets when the caller sends a non-empty value
    if body.teams_app_secret:
        openflow_config.TEAMS_APP_SECRET.value = body.teams_app_secret
    if body.metabase_password:
        openflow_config.METABASE_PASSWORD.value = body.metabase_password
    if body.llm_api_key:
        openflow_config.LLM_API_KEY.value = body.llm_api_key

    config = {
        **CONFIG_DATA,
        'openflow': {
            'teams_app_id': openflow_config.TEAMS_APP_ID.value,
            'teams_app_secret': openflow_config.TEAMS_APP_SECRET.value,
            'teams_tenant_id': openflow_config.TEAMS_TENANT_ID.value,
            'metabase_url': openflow_config.METABASE_URL.value,
            'metabase_username': openflow_config.METABASE_USERNAME.value,
            'metabase_password': openflow_config.METABASE_PASSWORD.value,
            'metabase_database_id': openflow_config.METABASE_DATABASE_ID.value,
            'schema_cache_minutes': openflow_config.SCHEMA_CACHE_MINUTES.value,
            'llm_base_url': openflow_config.LLM_BASE_URL.value,
            'llm_model': openflow_config.LLM_MODEL.value,
            'llm_api_key': openflow_config.LLM_API_KEY.value,
        },
    }

    await async_save_config(config)
    logger.info('OpenFlow settings updated by %s', user.email)

    return _current_settings()
