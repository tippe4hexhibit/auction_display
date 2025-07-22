<script>
  import { onMount } from 'svelte';
  import { getAuthHeaders } from '../utils/auth.js';
  
  export let lot = {};
  export let bidderNumber = '';
  export let bidHistory = [];
  export let logMessages = [];
  export let pacing = null;
  export let onAddBidder;
  export let onNextLot;
  export let onPrevLot;
  export let onFileUpload;
  export let onUndoBidder;
  export let onMergeBidders;
  
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
  let imageFileInput;
  let imageUploading = false;
  let showMerge = false;
  let sourceBidder = '';
  let targetBidder = '';

  function handleKeyPress(e) {
    if (e.key === 'Enter') {
      onAddBidder();
    }
  }

  async function handleImageUpload(files) {
    if (!files || files.length === 0 || !lot?.LotNumber) return;
    
    const file = files[0];
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }
    
    imageUploading = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE}/api/lot/${lot.LotNumber}/image`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });
      
      if (response.ok) {
        alert('Image uploaded successfully');
      } else {
        const error = await response.json();
        alert(`Upload failed: ${error.detail}`);
      }
    } catch (error) {
      alert('Upload failed: Network error');
    } finally {
      imageUploading = false;
    }
  }
  
  function handleImageFileSelect(event) {
    handleImageUpload(event.target.files);
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
  .drop-zone { border: 2px dashed #888; padding: 2rem; margin-top: 1rem; text-align: center; background: #fff; font-weight: bold; color: #555; }
  .drop-zone:hover { background: #eef; border-color: #55f; cursor: pointer; }
  .image-upload { background: #f0f8ff; border-color: #4CAF50; }
  .image-upload:hover { background: #e6f3ff; border-color: #45a049; }
  .image-upload button { 
    margin-top: 10px; 
    padding: 8px 16px; 
    background: #4CAF50; 
    color: white; 
    border: none; 
    border-radius: 4px; 
    cursor: pointer; 
  }
  .image-upload button:hover { background: #45a049; }
  .pacing-info { 
    margin-top: 1rem; 
    padding: 1rem; 
    background: #f0f8ff; 
    border-radius: 4px; 
    border-left: 4px solid #007bff; 
  }
  .pacing-suggestion { 
    font-weight: bold; 
    color: #28a745; 
  }
  .pacing-suggestion.warning { 
    color: #ffc107; 
  }
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
  .log-box { border:1px solid #ccc; height:150px; overflow-y:scroll; background: #000; color: #0f0; font-family: monospace; padding: 0.5rem; }
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
  
  {#if pacing}
    <div class="pacing-info">
      <h4>Pacing Feedback</h4>
      <p><strong>Current Duration:</strong> {pacing.current_duration}s</p>
      {#if pacing.average_duration}
        <p><strong>Average Duration:</strong> {pacing.average_duration}s</p>
      {/if}
      <p class="pacing-suggestion" class:warning={pacing.suggestion.includes('Consider')}>{pacing.suggestion}</p>
    </div>
  {/if}
</div>

<div class="section">
  <h3>Upload Files</h3>
  <div class="drop-zone"
       on:drop={(e) => { e.preventDefault(); onFileUpload(e.dataTransfer.files, '/api/upload/sale_program'); }}
       on:dragover={(e) => e.preventDefault()}>
    Drag & drop Sale Program Excel file here
  </div>
  <div class="drop-zone"
       on:drop={(e) => { e.preventDefault(); onFileUpload(e.dataTransfer.files, '/api/upload/buyer_list'); }}
       on:dragover={(e) => e.preventDefault()}>
    Drag & drop Buyer List Excel file here
  </div>
  {#if lot?.LotNumber}
    <div class="drop-zone image-upload"
         on:drop={(e) => { e.preventDefault(); handleImageUpload(e.dataTransfer.files); }}
         on:dragover={(e) => e.preventDefault()}>
      {imageUploading ? 'Uploading...' : `Drag & drop image for Lot ${lot.LotNumber} here`}
      <input type="file" accept="image/*" on:change={handleImageFileSelect} style="display: none;" bind:this={imageFileInput} />
      <button on:click={() => imageFileInput.click()} disabled={imageUploading}>
        {imageUploading ? 'Uploading...' : 'Or click to select image'}
      </button>
    </div>
  {/if}
</div>

<div class="section">
  <h3>Recent Entries</h3>
  {#if (bidHistory || []).length === 0}
    <p style="text-align:center; font-style:italic;">No bids recorded yet.</p>
  {:else}
    <table>
      <tr><th>Lot</th><th>Student</th><th>Buyer #</th><th>Buyer Name</th></tr>
      {#each bidHistory || [] as entry}
        <tr><td>{entry.LotNumber}</td><td>{entry.StudentName}</td><td>{entry.BuyerNumber}</td><td>{entry.BuyerName}</td></tr>
      {/each}
    </table>
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

<div class="section">
  <h3>Log</h3>
  <div class="log-box">
    {#each logMessages || [] as msg}
      <div>{msg}</div>
    {/each}
  </div>
</div>
