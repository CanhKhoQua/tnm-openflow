export type ConnectorStatus = {
	name: string;
	registered: boolean;
};

export const getConnectorStatus = async (token: string): Promise<ConnectorStatus[]> => {
	const res = await fetch('/openflow/status', {
		headers: { Authorization: `Bearer ${token}` }
	});
	if (!res.ok) throw new Error(await res.text());
	return res.json();
};

export const getTeamsWebhookUrl = (baseUrl: string) =>
	`${baseUrl}/openflow/teams/messages`;
