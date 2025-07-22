<script>
  export let saleData = [];
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .sale-list { height: 400px; overflow-y: scroll; border: 1px solid #ddd; padding: 0.5rem; background: white; }
  .sale-item { padding: 0.5rem; border-bottom: 1px solid #eee; cursor: pointer; }
  .sale-item:hover { background: #f5f5f5; }
  .sale-item:last-child { border-bottom: none; }
</style>

<div class="section">
  <h3>Sale List ({(saleData || []).length} lots)</h3>
  {#if (saleData || []).length === 0}
    <p style="text-align:center; font-style:italic;">No sale data loaded.</p>
  {:else}
    <div class="sale-list">
      {#each saleData || [] as item, index}
        <div class="sale-item">
          <strong>#{index + 1}</strong> - Lot {item.LotNumber}: {item.StudentName} ({item.Department})
        </div>
      {/each}
    </div>
  {/if}
</div>
