<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import {
		getConnectorStatus,
		getOpenflowSettings,
		getTeamsWebhookUrl,
		updateOpenflowSettings,
		type ConnectorStatus,
		type OpenflowSettingsPayload,
		type OpenflowSettingsResponse
	} from '$lib/apis/openflow';

	const i18n = getContext('i18n');

	let connectors: ConnectorStatus[] = [];
	let settings: OpenflowSettingsResponse | null = null;
	let loading = true;
	let saving = false;

	// Non-secret fields
	let teamsAppId = '';
	let teamsTenantId = '';
	let metabaseUrl = '';
	let metabaseUsername = '';
	let metabaseDatabaseId = 1;
	let schemaCacheMinutes = 60;
	let llmBaseUrl = '';
	let llmModel = '';

	// Secret fields — always empty on load; only sent if user types a value
	let teamsAppSecret = '';
	let metabasePassword = '';
	let llmApiKey = '';

	onMount(async () => {
		try {
			[connectors, settings] = await Promise.all([
				getConnectorStatus($user?.token ?? ''),
				getOpenflowSettings($user?.token ?? '')
			]);
			populateForm(settings);
		} catch {
			toast.error($i18n.t('Failed to load OpenFlow configuration'));
		} finally {
			loading = false;
		}
	});

	function populateForm(s: OpenflowSettingsResponse) {
		teamsAppId = s.teams_app_id;
		teamsTenantId = s.teams_tenant_id;
		metabaseUrl = s.metabase_url;
		metabaseUsername = s.metabase_username;
		metabaseDatabaseId = s.metabase_database_id;
		schemaCacheMinutes = s.schema_cache_minutes;
		llmBaseUrl = s.llm_base_url;
		llmModel = s.llm_model;
		// secrets intentionally left blank — server never returns them
	}

	async function save() {
		saving = true;
		try {
			const payload: OpenflowSettingsPayload = {
				teams_app_id: teamsAppId,
				teams_app_secret: teamsAppSecret,
				teams_tenant_id: teamsTenantId,
				metabase_url: metabaseUrl,
				metabase_username: metabaseUsername,
				metabase_password: metabasePassword,
				metabase_database_id: metabaseDatabaseId,
				schema_cache_minutes: schemaCacheMinutes,
				llm_base_url: llmBaseUrl,
				llm_model: llmModel,
				llm_api_key: llmApiKey
			};
			settings = await updateOpenflowSettings($user?.token ?? '', payload);
			// Clear secret inputs after successful save
			teamsAppSecret = '';
			metabasePassword = '';
			llmApiKey = '';
			toast.success($i18n.t('Settings saved'));
		} catch {
			toast.error($i18n.t('Failed to save settings'));
		} finally {
			saving = false;
		}
	}

	$: webhookUrl = getTeamsWebhookUrl(window?.location?.origin ?? '');
</script>

<div class="flex flex-col gap-8 p-4 max-w-2xl">
	<!-- Header -->
	<div>
		<h2 class="text-lg font-semibold">{$i18n.t('Bot Integrations')}</h2>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
			{$i18n.t('Configure TNM OpenFlow connectors and credentials.')}
		</p>
	</div>

	{#if loading}
		<div class="text-sm text-gray-400">{$i18n.t('Loading...')}</div>
	{:else}
		<!-- Connector status -->
		<section class="flex flex-col gap-3">
			<h3 class="text-sm font-semibold">{$i18n.t('Connector Status')}</h3>
			{#if connectors.length === 0}
				<div class="text-sm text-gray-400">{$i18n.t('No connectors registered.')}</div>
			{:else}
				{#each connectors as connector}
					<div
						class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3"
					>
						<div class="flex items-center gap-3">
							<span
								class="h-2.5 w-2.5 rounded-full {connector.registered
									? 'bg-green-500'
									: 'bg-gray-400'}"
							/>
							<span class="font-medium capitalize">{connector.name}</span>
						</div>
						<span class="text-xs text-gray-500">
							{connector.registered ? $i18n.t('Active') : $i18n.t('Inactive')}
						</span>
					</div>
				{/each}
			{/if}
		</section>

		<!-- Webhook URL -->
		<section class="flex flex-col gap-2">
			<h3 class="text-sm font-semibold">{$i18n.t('Microsoft Teams Webhook URL')}</h3>
			<div class="flex items-center gap-2">
				<input
					type="text"
					readonly
					value={webhookUrl}
					class="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm font-mono"
				/>
				<button
					type="button"
					class="px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-700 text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition"
					on:click={() => {
						navigator.clipboard.writeText(webhookUrl);
						toast.success($i18n.t('Copied'));
					}}
				>
					{$i18n.t('Copy')}
				</button>
			</div>
			<p class="text-xs text-gray-400">
				{$i18n.t('Register this URL as the messaging endpoint in your Azure Bot resource.')}
			</p>
		</section>

		<!-- Settings form -->
		<form on:submit|preventDefault={save} class="flex flex-col gap-6">
			<!-- Teams -->
			<section class="flex flex-col gap-3">
				<h3 class="text-sm font-semibold">{$i18n.t('Microsoft Teams')}</h3>
				<div class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">{$i18n.t('App ID')}</span>
						<input
							type="text"
							bind:value={teamsAppId}
							placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
							class="input-field"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">
							{$i18n.t('App Secret')}
							{#if settings?.teams_app_secret_set}
								<span class="ml-1 text-green-500">&#10003; {$i18n.t('set')}</span>
							{/if}
						</span>
						<input
							type="password"
							bind:value={teamsAppSecret}
							placeholder={settings?.teams_app_secret_set
								? $i18n.t('Leave blank to keep current')
								: ''}
							class="input-field"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">
							{$i18n.t('Tenant ID')}
							<span class="text-gray-400 ml-1">({$i18n.t('optional')})</span>
						</span>
						<input
							type="text"
							bind:value={teamsTenantId}
							placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
							class="input-field"
						/>
					</label>
				</div>
			</section>

			<!-- Metabase -->
			<section class="flex flex-col gap-3">
				<h3 class="text-sm font-semibold">{$i18n.t('Metabase')}</h3>
				<div class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">{$i18n.t('URL')}</span>
						<input
							type="text"
							bind:value={metabaseUrl}
							placeholder="http://metabase:3000"
							class="input-field"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">{$i18n.t('Username')}</span>
						<input
							type="text"
							bind:value={metabaseUsername}
							placeholder="admin@example.com"
							class="input-field"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">
							{$i18n.t('Password')}
							{#if settings?.metabase_password_set}
								<span class="ml-1 text-green-500">&#10003; {$i18n.t('set')}</span>
							{/if}
						</span>
						<input
							type="password"
							bind:value={metabasePassword}
							placeholder={settings?.metabase_password_set
								? $i18n.t('Leave blank to keep current')
								: ''}
							class="input-field"
						/>
					</label>
					<div class="grid grid-cols-2 gap-3">
						<label class="flex flex-col gap-1">
							<span class="text-xs text-gray-500">{$i18n.t('Database ID')}</span>
							<input type="number" min="1" bind:value={metabaseDatabaseId} class="input-field" />
						</label>
						<label class="flex flex-col gap-1">
							<span class="text-xs text-gray-500">{$i18n.t('Schema Cache (min)')}</span>
							<input type="number" min="1" bind:value={schemaCacheMinutes} class="input-field" />
						</label>
					</div>
				</div>
			</section>

			<!-- LLM -->
			<section class="flex flex-col gap-3">
				<h3 class="text-sm font-semibold">{$i18n.t('LLM (NL-to-SQL)')}</h3>
				<div class="flex flex-col gap-3">
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">{$i18n.t('Base URL')}</span>
						<input
							type="text"
							bind:value={llmBaseUrl}
							placeholder="http://ollama:11434/v1"
							class="input-field"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">{$i18n.t('Model')}</span>
						<input type="text" bind:value={llmModel} placeholder="llama3.2" class="input-field" />
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-xs text-gray-500">
							{$i18n.t('API Key')}
							{#if settings?.llm_api_key_set}
								<span class="ml-1 text-green-500">&#10003; {$i18n.t('set')}</span>
							{/if}
							<span class="text-gray-400 ml-1"
								>({$i18n.t('optional — leave blank for local Ollama')})</span
							>
						</span>
						<input
							type="password"
							bind:value={llmApiKey}
							placeholder={settings?.llm_api_key_set ? $i18n.t('Leave blank to keep current') : ''}
							class="input-field"
						/>
					</label>
				</div>
			</section>

			<div class="flex justify-end">
				<button
					type="submit"
					disabled={saving}
					class="px-5 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium hover:opacity-80 transition disabled:opacity-50"
				>
					{saving ? $i18n.t('Saving…') : $i18n.t('Save')}
				</button>
			</div>
		</form>
	{/if}
</div>

<style>
	.input-field {
		@apply w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white;
	}
</style>
