<script>
  import { onMount, afterUpdate } from 'svelte';
  import { getAuthHeaders } from '../utils/auth.js';
  
  export let lot = {};
  export let bidderNumber = '';
  export let bidHistory = [];
  export let onAddBidder;
  export let onNextLot;
  export let onPrevLot;
  export let onUndoBidder;
  export let onMergeBidders;
  
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
  let showMerge = false;
  let sourceBidder = '';
  let targetBidder = '';
  let bidderTableContainer;

  function handleKeyPress(e) {
    if (e.key === 'Enter') {
      onAddBidder();
    }
  }

  // Auto-scroll to bottom when bidHistory changes
  $: if (bidHistory && bidHistory.length > 0 && bidderTableContainer) {
    setTimeout(() => {
      bidderTableContainer.scrollTop = bidderTableContainer.scrollHeight;
    }, 100);
  }

  
  function showMergeForm() {
    showMerge = true;
    sourceBidder = '';
    targetBidder = '';
  }
  
  async function handleMerge() {
    if (!sourceBidder || !targetBidder) return;
    
    if (sourceBidder === targetBidder) {
      alert('Source and target bidders cannot be the same');
      return;
    }
    
    const confirmed = confirm(`Are you sure you want to merge bidder ${sourceBidder} into bidder ${targetBidder}? This cannot be undone.`);
    if (!confirmed) return;
    
    await onMergeBidders(parseInt(sourceBidder), parseInt(targetBidder));
    showMerge = false;
  }
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .admin-tools { 
    margin-top: 1rem; 
    display: flex; 
    gap: 0.5rem; 
  }
  .undo-btn { 
    background: #ffc107; 
    color: #212529; 
  }
  .undo-btn:hover { 
    background: #e0a800; 
  }
  .merge-btn { 
    background: #17a2b8; 
    color: white; 
  }
  .merge-btn:hover { 
    background: #138496; 
  }
  .merge-form { 
    margin-top: 1rem; 
    padding: 1rem; 
    background: #fff3cd; 
    border-radius: 4px; 
    border: 1px solid #ffeaa7; 
  }
  .merge-inputs { 
    display: flex; 
    align-items: center; 
    gap: 0.5rem; 
    margin: 0.5rem 0; 
  }
  .merge-inputs input { 
    width: 120px; 
  }
  .merge-warning { 
    font-size: 0.9rem; 
    color: #856404; 
    margin: 0.5rem 0 0 0; 
  }
  .bidder-table-container { max-height: 300px; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 0.5rem; border: 1px solid #aaa; text-align: left; }
  .controls { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .controls input { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
  .controls button { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
  .controls button:hover { background: #0056b3; }
</style>

<div class="section">
  <p><strong>Current Lot:</strong>
    {lot?.LotNumber ? `${lot.LotNumber} - ${lot.StudentName} (${lot.Department})` : 'No lot selected'}</p>
  <div class="controls">
    <button on:click={onPrevLot}>Previous Lot</button>
    <button on:click={onNextLot}>Next Lot</button>
    <input placeholder="Enter Bidder Number" bind:value={bidderNumber} on:keypress={handleKeyPress} />
    <button on:click={onAddBidder}>Add Bidder</button>
  </div>
  
</div>


<div class="section">
  <h3>Buyers for Lot {lot?.LotNumber || 'N/A'}</h3>
  {#if (bidHistory || []).length === 0}
    <p style="text-align:center; font-style:italic;">No bids recorded yet.</p>
  {:else}
    <div class="bidder-table-container" bind:this={bidderTableContainer}>
      <table>
        <tr><th>Lot</th><th>Student</th><th>Buyer #</th><th>Buyer Name</th></tr>
        {#each bidHistory || [] as entry}
          <tr><td>{entry.LotNumber}</td><td>{entry.StudentName}</td><td>{entry.BuyerNumber}</td><td>{entry.BuyerName}</td></tr>
        {/each}
      </table>
    </div>
    <div class="admin-tools">
      <button on:click={onUndoBidder} class="undo-btn">Undo Last Bidder</button>
      <button on:click={showMergeForm} class="merge-btn">Merge Bidders</button>
    </div>
  {/if}
  
  {#if showMerge}
    <div class="merge-form">
      <h4>Merge Bidders</h4>
      <div class="merge-inputs">
        <input type="number" placeholder="Source Bidder #" bind:value={sourceBidder} />
        <span>→</span>
        <input type="number" placeholder="Target Bidder #" bind:value={targetBidder} />
        <button on:click={handleMerge} disabled={!sourceBidder || !targetBidder}>Merge</button>
        <button on:click={() => showMerge = false}>Cancel</button>
      </div>
      <p class="merge-warning">⚠️ This will merge all bids from source bidder into target bidder. This cannot be undone.</p>
    </div>
  {/if}
</div>
