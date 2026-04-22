export type ConnectorStatus = {
	name: string;
	registered: boolean;
};

export type OpenflowSettingsResponse = {
	teams_app_id: string;
	teams_app_secret_set: boolean;
	teams_tenant_id: string;
	metabase_url: string;
	metabase_username: string;
	metabase_password_set: boolean;
	metabase_database_id: number;
	schema_cache_minutes: number;
	llm_base_url: string;
	llm_model: string;
	llm_api_key_set: boolean;
};

export type OpenflowSettingsPayload = {
	teams_app_id: string;
	teams_app_secret: string;
	teams_tenant_id: string;
	metabase_url: string;
	metabase_username: string;
	metabase_password: string;
	metabase_database_id: number;
	schema_cache_minutes: number;
	llm_base_url: string;
	llm_model: string;
	llm_api_key: string;
};

export const getConnectorStatus = async (token: string): Promise<ConnectorStatus[]> => {
	const res = await fetch('/openflow/status', {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error(await res.text());
	return res.json();
};

export const getTeamsWebhookUrl = (baseUrl: string) => `${baseUrl}/openflow/teams/messages`;

export const getOpenflowSettings = async (token: string): Promise<OpenflowSettingsResponse> => {
	const res = await fetch('/openflow/settings', {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error(await res.text());
	return res.json();
};

export const updateOpenflowSettings = async (
	token: string,
	payload: OpenflowSettingsPayload
): Promise<OpenflowSettingsResponse> => {
	const res = await fetch('/openflow/settings', {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
	if (!res.ok) throw new Error(await res.text());
	return res.json();
};
