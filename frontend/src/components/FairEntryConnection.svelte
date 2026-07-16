<script>
  export let settings = {};
  export let onSaveSettings;

  let username = '';
  let password = '';
  let fairTitle = '';
  let saving = false;

  let initialized = false;
  $: if (!initialized && settings && settings.username !== undefined) {
    username = settings.username || '';
    fairTitle = settings.fair_title || '';
    initialized = true;
  }

  async function saveSettings() {
    saving = true;
    try {
      await onSaveSettings({ username, password, fair_title: fairTitle });
      password = '';
    } finally {
      saving = false;
    }
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
  .hint { margin-top: 0.5rem; font-size: 0.85rem; color: #666; }
</style>

<div class="section">
  <h3>FairEntry Connection</h3>
  <p class="hint">Shared login used by both the Buyer List and Sale List sync features.</p>

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

  <button class="btn" on:click={saveSettings} disabled={saving}>
    {saving ? 'Saving...' : 'Save Settings'}
  </button>
</div>
