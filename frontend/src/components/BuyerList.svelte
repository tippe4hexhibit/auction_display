<script>
  export let buyerData = [];
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .buyer-list { height: 400px; overflow-y: scroll; border: 1px solid #ddd; padding: 0.5rem; background: white; }
  .buyer-item { padding: 0.5rem; border-bottom: 1px solid #eee; cursor: pointer; }
  .buyer-item:hover { background: #f5f5f5; }
  .buyer-item:last-child { border-bottom: none; }
</style>

<div class="section">
  <h3>Buyer List ({(buyerData || []).length} buyers)</h3>
  {#if (buyerData || []).length === 0}
    <p style="text-align:center; font-style:italic;">No buyer data loaded.</p>
  {:else}
    <div class="buyer-list">
      {#each buyerData || [] as buyer}
        <div class="buyer-item">
          <strong>#{buyer.Identifier}</strong> - {buyer.Name}
        </div>
      {/each}
    </div>
  {/if}
</div>
