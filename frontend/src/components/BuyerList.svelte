<script>
  export let buyerData = [];
  export let onFileUpload;
  
  $: sortedBuyerData = (buyerData || []).sort((a, b) => {
    const aId = parseInt(a.Identifier) || 0;
    const bId = parseInt(b.Identifier) || 0;
    return aId - bId;
  });
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .buyer-list { height: 400px; overflow-y: scroll; border: 1px solid #ddd; padding: 0.5rem; background: white; }
  .buyer-item { padding: 0.5rem; border-bottom: 1px solid #eee; cursor: pointer; }
  .buyer-item:hover { background: #f5f5f5; }
  .buyer-item:last-child { border-bottom: none; }
  .drop-zone { border: 2px dashed #888; padding: 2rem; margin-top: 1rem; text-align: center; background: #fff; font-weight: bold; color: #555; }
  .drop-zone:hover { background: #eef; border-color: #55f; cursor: pointer; }
</style>

<div class="section">
  <h3>Buyer List ({(buyerData || []).length} buyers)</h3>
  <div class="drop-zone"
       on:drop={(e) => { e.preventDefault(); onFileUpload(e.dataTransfer.files, '/api/upload/buyer_list'); }}
       on:dragover={(e) => e.preventDefault()}
       on:click={() => document.getElementById('buyer-file-input').click()}>
    Drag & drop Buyer List Excel file here or click to browse
    <input id="buyer-file-input" type="file" accept=".xlsx,.xls" style="display: none;" 
           on:change={(e) => onFileUpload(e.target.files, '/api/upload/buyer_list')} />
  </div>
  {#if (buyerData || []).length === 0}
    <p style="text-align:center; font-style:italic;">No buyer data loaded.</p>
  {:else}
    <div class="buyer-list">
      {#each sortedBuyerData as buyer}
        <div class="buyer-item">
          <strong>#{buyer.Identifier}</strong> - {buyer.Name}
        </div>
      {/each}
    </div>
  {/if}
</div>
