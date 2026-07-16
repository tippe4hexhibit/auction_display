<script>
  export let options = [];
  export let selectedId = null;
  export let onRefresh;
  export let onSelect;

  let refreshing = false;

  async function refresh() {
    refreshing = true;
    try {
      await onRefresh();
    } finally {
      refreshing = false;
    }
  }

  function handleChange(e) {
    const id = parseInt(e.target.value, 10);
    if (!Number.isNaN(id)) onSelect(id);
  }
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .row { display: flex; align-items: center; gap: 0.5rem; }
  select { flex: 1; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
  .btn { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
  .btn:hover:not(:disabled) { background: #0056b3; }
  .btn:disabled { background: #6c757d; cursor: not-allowed; }
  .hint { margin-top: 0.5rem; font-size: 0.85rem; color: #666; }
</style>

<div class="section">
  <h3>Sale Order</h3>
  <div class="row">
    <select value={selectedId ?? ''} on:change={handleChange} disabled={(options || []).length === 0}>
      {#if (options || []).length === 0}
        <option value="" disabled>No sale orders found</option>
      {/if}
      {#each options || [] as option}
        <option value={option.id}>{option.name} ({option.entry_count} entries)</option>
      {/each}
    </select>
    <button class="btn" on:click={refresh} disabled={refreshing}>
      {refreshing ? 'Refreshing...' : 'Refresh'}
    </button>
  </div>
  <p class="hint">
    {#if (options || []).length === 0}
      Click Refresh to query FairEntry for the Sale Orders in this Fair.
    {:else if (options || []).length === 1}
      Only one Sale Order exists — it's selected automatically.
    {:else}
      Select which Sale Order should drive the Sale List.
    {/if}
  </p>
</div>
