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
  export let onScratchBidder;

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

  // Ctrl+Z / Cmd+Z undoes the most recent buyer entry, same action as the
  // "Undo Last Buyer" button. Only active while this tab is mounted.
  function handleGlobalKeydown(e) {
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      onUndoBidder();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleGlobalKeydown);
    return () => window.removeEventListener('keydown', handleGlobalKeydown);
  });

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
      alert('Source and target buyers cannot be the same');
      return;
    }

    const confirmed = confirm(`Are you sure you want to merge buyer ${sourceBidder} into buyer ${targetBidder}? This cannot be undone.`);
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
  .scratch-cell { text-align: center; }
  .scratch-btn { background: none; border: none; padding: 0.2rem 0.4rem; font-size: 1.1rem; cursor: pointer; }
  .scratch-btn:hover { opacity: 0.7; }
  .scratched-row td { color: #dc3545; text-decoration: line-through; }
  .controls { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .controls input { padding: 0.85rem; border: 1px solid #ccc; border-radius: 4px; font-size: 1.4rem; width: 260px; box-sizing: border-box; }
  .controls button { padding: 0.85rem 1.7rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1.4rem; }
  .controls button:hover { background: #0056b3; }
  .current-lot-label { font-size: 1.4rem; }
</style>

<div class="section">
  <p class="current-lot-label"><strong>Current Lot:</strong>
    {lot?.LotNumber ? `${lot.LotNumber} - ${lot.StudentName} (${lot.Department})` : 'No lot selected'}</p>
  <div class="controls">
    <button on:click={onPrevLot}>Previous Lot</button>
    <button on:click={onNextLot}>Next Lot</button>
    <input placeholder="Enter Buyer Number" bind:value={bidderNumber} on:keypress={handleKeyPress} />
    <button on:click={onAddBidder}>Add Buyer</button>
  </div>

</div>


<div class="section">
  <h3>Buyers for Lot {lot?.LotNumber || 'N/A'}</h3>
  {#if (bidHistory || []).length === 0}
    <p style="text-align:center; font-style:italic;">No bids recorded yet.</p>
  {:else}
    <div class="bidder-table-container" bind:this={bidderTableContainer}>
      <table>
        <thead>
          <tr><th>Lot</th><th>Student</th><th>Buyer #</th><th>Buyer Name</th><th></th></tr>
        </thead>
        <tbody>
          {#each bidHistory || [] as entry}
            <tr class:scratched-row={entry.Scratched}>
              <td>{entry.LotNumber}</td>
              <td>{entry.StudentName}</td>
              <td>{entry.BuyerNumber}</td>
              <td>{entry.BuyerName}</td>
              <td class="scratch-cell">
                {#if !entry.Scratched}
                  <button class="scratch-btn" on:click={() => onScratchBidder(entry.Id)} title="Remove {entry.BuyerName}">🗑️</button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <div class="admin-tools">
      <button on:click={onUndoBidder} class="undo-btn">Undo Last Buyer</button>
      <button on:click={showMergeForm} class="merge-btn">Merge Buyers</button>
    </div>
  {/if}

  {#if showMerge}
    <div class="merge-form">
      <h4>Merge Buyers</h4>
      <div class="merge-inputs">
        <input type="number" placeholder="Source Buyer #" bind:value={sourceBidder} />
        <span>→</span>
        <input type="number" placeholder="Target Buyer #" bind:value={targetBidder} />
        <button on:click={handleMerge} disabled={!sourceBidder || !targetBidder}>Merge</button>
        <button on:click={() => showMerge = false}>Cancel</button>
      </div>
      <p class="merge-warning">⚠️ This will merge all bids from source buyer into target buyer. This cannot be undone.</p>
    </div>
  {/if}
</div>
