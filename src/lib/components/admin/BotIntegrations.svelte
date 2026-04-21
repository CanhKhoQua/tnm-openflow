<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import { getConnectorStatus, getTeamsWebhookUrl, type ConnectorStatus } from '$lib/apis/openflow';

	const i18n = getContext('i18n');

	let connectors: ConnectorStatus[] = [];
	let loading = true;

	onMount(async () => {
		try {
			connectors = await getConnectorStatus($user?.token ?? '');
		} catch (e) {
			toast.error('Failed to load connector status');
		} finally {
			loading = false;
		}
	});

	$: webhookUrl = getTeamsWebhookUrl(window?.location?.origin ?? '');
</script>

<div class="flex flex-col gap-6 p-4">
	<div>
		<h2 class="text-lg font-semibold">{$i18n.t('Bot Integrations')}</h2>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
			{$i18n.t('Manage platform connector registrations for TNM OpenFlow.')}
		</p>
	</div>

	{#if loading}
		<div class="text-sm text-gray-400">{$i18n.t('Loading...')}</div>
	{:else if connectors.length === 0}
		<div class="text-sm text-gray-400">{$i18n.t('No connectors registered.')}</div>
	{:else}
		<div class="flex flex-col gap-3">
			{#each connectors as connector}
				<div class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-4 py-3">
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
		</div>
	{/if}

	<div>
		<h3 class="text-sm font-semibold mb-2">{$i18n.t('Microsoft Teams Webhook URL')}</h3>
		<div class="flex items-center gap-2">
			<input
				type="text"
				readonly
				value={webhookUrl}
				class="flex-1 rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm font-mono"
			/>
			<button
				class="px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-700 text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition"
				on:click={() => {
					navigator.clipboard.writeText(webhookUrl);
					toast.success($i18n.t('Copied to clipboard'));
				}}
			>
				{$i18n.t('Copy')}
			</button>
		</div>
		<p class="text-xs text-gray-400 mt-1">
			{$i18n.t('Register this URL as the messaging endpoint in your Azure Bot resource.')}
		</p>
	</div>
</div>
