<script>
  export let logMessages = [];
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .log-box { border:1px solid #ccc; height:400px; overflow-y:scroll; background: #000; color: #0f0; font-family: monospace; padding: 0.5rem; }
  .clear-btn { padding: 0.5rem 1rem; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 0.5rem; }
  .clear-btn:hover { background: #c82333; }
</style>

<div class="section">
  <h3>System Logs</h3>
  <div class="log-box">
    {#each logMessages || [] as msg}
      <div>{msg}</div>
    {/each}
    {#if (logMessages || []).length === 0}
      <div style="color: #666;">No log messages yet...</div>
    {/if}
  </div>
  <button class="clear-btn" on:click={() => { logMessages = []; localStorage.removeItem('auction-logs'); }}>
    Clear Logs
  </button>
</div>
