<script>
  export let settings = {};
  export let onSaveSettings;
  export let onToggleSync;
  export let onSyncNow;

  let username = '';
  let password = '';
  let fairTitle = '';
  let syncIntervalMinutes = 15;
  let saving = false;
  let syncing = false;
  let toggling = false;
  let syncNowMessage = '';

  let initialized = false;
  $: if (!initialized && settings && settings.username !== undefined) {
    username = settings.username || '';
    fairTitle = settings.fair_title || '';
    syncIntervalMinutes = settings.sync_interval_minutes || 15;
    initialized = true;
  }

  async function saveSettings() {
    saving = true;
    try {
      await onSaveSettings({ username, password, fair_title: fairTitle, sync_interval_minutes: syncIntervalMinutes });
      password = '';
    } finally {
      saving = false;
    }
  }

  async function toggleSync() {
    toggling = true;
    try {
      await onToggleSync(!settings.sync_enabled);
    } finally {
      toggling = false;
    }
  }

  async function syncNow() {
    syncing = true;
    syncNowMessage = '';
    try {
      const result = await onSyncNow();
      syncNowMessage = result && result.message ? result.message : '';
    } finally {
      syncing = false;
    }
  }

  function formatTimestamp(iso) {
    if (!iso) return 'never';
    return new Date(iso).toLocaleString();
  }
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .form-group { margin: 0.5rem 0; }
  .form-group label { display: block; margin-bottom: 0.25rem; font-weight: bold; }
  .form-group input { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
  .btn { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 0.5rem; }
  .btn:hover:not(:disabled) { background: #0056b3; }
  .btn:disabled { background: #6c757d; cursor: not-allowed; }
  .btn-toggle-on { background: #28a745; }
  .btn-toggle-on:hover:not(:disabled) { background: #1e7e34; }
  .btn-toggle-off { background: #6c757d; }
  .status { margin-top: 1rem; padding: 0.75rem; border-radius: 4px; background: white; border: 1px solid #ddd; }
  .status-row { display: flex; justify-content: space-between; margin: 0.25rem 0; }
  .badge { padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
  .badge-on { background: #d4edda; color: #155724; }
  .badge-off { background: #e2e3e5; color: #383d41; }
  .status-success { color: #28a745; }
  .status-error { color: #dc3545; }
  .sync-now-msg { margin-top: 0.5rem; font-style: italic; }
</style>

<div class="section">
  <h3>FairEntry Auto-Sync</h3>

  <div class="form-group">
    <label for="fe-username">FairEntry Username</label>
    <input id="fe-username" type="text" bind:value={username} placeholder="username@example.com" />
  </div>
  <div class="form-group">
    <label for="fe-password">FairEntry Password</label>
    <input id="fe-password" type="password" bind:value={password} placeholder={settings.has_password ? '•••••• (saved — leave blank to keep)' : 'Enter password'} />
  </div>
  <div class="form-group">
    <label for="fe-fair-title">Fair Title</label>
    <input id="fe-fair-title" type="text" bind:value={fairTitle} placeholder="2026 County Fair" />
  </div>
  <div class="form-group">
    <label for="fe-interval">Sync Interval (minutes)</label>
    <input id="fe-interval" type="number" min="1" bind:value={syncIntervalMinutes} />
  </div>

  <button class="btn" on:click={saveSettings} disabled={saving}>
    {saving ? 'Saving...' : 'Save Settings'}
  </button>
  <button
    class="btn"
    class:btn-toggle-on={!settings.sync_enabled}
    class:btn-toggle-off={settings.sync_enabled}
    on:click={toggleSync}
    disabled={toggling}
  >
    {settings.sync_enabled ? 'Disable Auto-Sync' : 'Enable Auto-Sync'}
  </button>
  <button class="btn" on:click={syncNow} disabled={syncing}>
    {syncing ? 'Syncing...' : 'Sync Now'}
  </button>

  {#if syncNowMessage}
    <p class="sync-now-msg">{syncNowMessage}</p>
  {/if}

  <div class="status">
    <div class="status-row">
      <span>Auto-Sync:</span>
      <span class="badge" class:badge-on={settings.sync_enabled} class:badge-off={!settings.sync_enabled}>
        {settings.sync_enabled ? 'ON' : 'OFF'}
      </span>
    </div>
    <div class="status-row">
      <span>Last Sync:</span>
      <span>{formatTimestamp(settings.last_sync_at)}</span>
    </div>
    <div class="status-row">
      <span>Status:</span>
      <span class:status-success={settings.last_sync_status === 'success'} class:status-error={settings.last_sync_status === 'error'}>
        {settings.last_sync_status || 'never'}
      </span>
    </div>
    {#if settings.last_sync_message}
      <div class="status-row">
        <span>Message:</span>
        <span>{settings.last_sync_message}</span>
      </div>
    {/if}
  </div>
</div>
