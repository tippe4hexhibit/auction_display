<script>
  import { onMount } from 'svelte';
  let lot = {};
  let bidderNumber = '';
  let ws;
  let saleData = [];
  let buyerData = [];
  let bidHistory = [];
  let logMessages = [];
  let currentTab = 'main';
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  async function fetchSaleData() {
    const res = await fetch(`${API_BASE}/api/sale`);
    const data = await res.json();
    saleData = Array.isArray(data) ? data : [];
  }

  async function fetchBuyerData() {
    const res = await fetch(`${API_BASE}/api/buyers`);
    const data = await res.json();
    buyerData = Array.isArray(data) ? data : [];
  }

  onMount(() => {
    ws = new WebSocket(API_BASE.replace('http', 'ws') + '/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      const timestamp = new Date().toLocaleTimeString();
      if (data.type === 'log' && data.message) {
        logMessages = [...logMessages, `${timestamp}: ${data.message}`];
      } else {
        logMessages = [...logMessages];
      }
      if (data.lot) lot = data.lot;
      if (Array.isArray(data.bidders)) {
        bidHistory = [
          ...bidHistory,
          {
            LotNumber: lot.LotNumber,
            StudentName: lot.StudentName,
            BuyerNumber: data.bidders.at(-1)?.Identifier,
            BuyerName: data.bidders.at(-1)?.Name
          }
        ].slice(-15);
      }
    };
    fetchSaleData();
    fetchBuyerData();
  });

  async function addBidder() {
    if (bidderNumber) {
      await fetch(`${API_BASE}/api/bidder/add/${bidderNumber}`, { method: 'POST' });
      bidderNumber = '';
    }
  }

  async function nextLot() {
    await fetch(`${API_BASE}/api/lot/next`, { method: 'POST' });
  }

  async function prevLot() {
    await fetch(`${API_BASE}/api/lot/prev`, { method: 'POST' });
  }

  async function handleFileUpload(files, endpoint) {
    const formData = new FormData();
    formData.append('file', files[0]);
    await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: formData });
    alert('Upload complete');
    await fetchSaleData();
    await fetchBuyerData();
  }
</script>

<!-- NOTE: We REMOVE (arr || []) from {#each} because Svelte needs the raw array -->
<!-- We ENSURE in code they are always arrays -->


<style>
  .tab-buttons button { margin-right: 0.5rem; }
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .drop-zone { border: 2px dashed #888; padding: 2rem; margin-top: 1rem; text-align: center; background: #fff; font-weight: bold; color: #555; }
  .drop-zone:hover { background: #eef; border-color: #55f; cursor: pointer; }
  .log-box { border:1px solid #ccc; height:150px; overflow-y:scroll; background: #000; color: #0f0; font-family: monospace; padding: 0.5rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 0.5rem; border: 1px solid #aaa; text-align: left; }
</style>

<div>
  <h2>Admin Console</h2>

  <div class="tab-buttons">
    <button on:click={() => currentTab = 'main'}>Main</button>
    <button on:click={() => currentTab = 'sale'}>Sale List</button>
    <button on:click={() => currentTab = 'buyers'}>Buyer List</button>
  </div>

  {#if currentTab === 'main'}
    <div class="section">
      <p><strong>Current Lot:</strong>
        {lot?.LotNumber ? `${lot.LotNumber} - ${lot.StudentName} (${lot.Department})` : 'No lot selected'}</p>
      <button on:click={prevLot}>Previous Lot</button>
      <button on:click={nextLot}>Next Lot</button>
      <input placeholder="Enter Bidder Number" bind:value={bidderNumber} on:keypress={(e) => e.key === 'Enter' && addBidder()} />
      <button on:click={addBidder}>Add Bidder</button>
    </div>

    <div class="section">
      <h3>Upload Files</h3>
      <div class="drop-zone"
           on:drop={(e) => { e.preventDefault(); handleFileUpload(e.dataTransfer.files, '/api/upload/sale_program'); }}
           on:dragover={(e) => e.preventDefault()}>
        Drag & drop Sale Program Excel file here
      </div>
      <div class="drop-zone"
           on:drop={(e) => { e.preventDefault(); handleFileUpload(e.dataTransfer.files, '/api/upload/buyer_list'); }}
           on:dragover={(e) => e.preventDefault()}>
        Drag & drop Buyer List Excel file here
      </div>
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
  {:else if currentTab === 'sale'}
    <div class="section">
      <h3>Sale List</h3>
      {#if (saleData || []).length === 0}
        <p style="text-align:center; font-style:italic;">No sale data loaded.</p>
      {:else}
        <div style="height:300px; overflow-y:scroll;">
          {#each saleData || [] as item}
            <div>{item.LotNumber} - {item.StudentName} ({item.Department})</div>
          {/each}
        </div>
      {/if}
    </div>
  {:else if currentTab === 'buyers'}
    <div class="section">
      <h3>Buyer List</h3>
      {#if (buyerData || []).length === 0}
        <p style="text-align:center; font-style:italic;">No buyer data loaded.</p>
      {:else}
        <div style="height:300px; overflow-y:scroll;">
          {#each buyerData || [] as buyer}
            <div>{buyer.Identifier} - {buyer.Name}</div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
