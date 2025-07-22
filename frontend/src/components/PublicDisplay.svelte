<script>
  import { onMount } from 'svelte';
  let lot = {};
  let bidders = [];
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  async function fetchInitialState() {
    try {
      const stateRes = await fetch(`${API_BASE}/api/state`);
      const stateData = await stateRes.json();
      if (stateData.lot) {
        lot = stateData.lot;
        bidders = stateData.bidders || [];
      }
    } catch (error) {
      console.error('Failed to fetch initial state:', error);
    }
  }

  onMount(() => {
    const ws = new WebSocket(API_BASE.replace('http', 'ws') + '/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.lot) lot = data.lot;
      if (Array.isArray(data.bidders)) bidders = data.bidders;
    };
    
    // Fetch initial data on mount
    fetchInitialState();
  });
</script>

<style>
  .public-display {
    position: relative;
    width: 100vw;
    height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    overflow: hidden;
  }
  
  .lot-image {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 60%;
    max-height: 60%;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
  
  .lot-image img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: white;
  }
  
  .lot-image-placeholder {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    height: 300px;
    border: 3px dashed rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
  }
  
  .placeholder-content {
    text-align: center;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .placeholder-content svg {
    margin-bottom: 15px;
    opacity: 0.6;
  }
  
  .placeholder-content p {
    margin: 0;
    font-size: 18px;
    font-weight: 500;
  }
  
  .lot-info {
    position: absolute;
    bottom: 30px;
    left: 30px;
    right: 30px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    backdrop-filter: blur(10px);
  }
  
  .lot-info h2 {
    margin: 0 0 15px 0;
    font-size: 2rem;
    font-weight: bold;
  }
  
  .bidders-section {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 15px;
  }
  
  .bidder-item {
    background: rgba(255, 255, 255, 0.2);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 1.1rem;
    font-weight: 500;
  }
  
  .clock {
    position: absolute;
    top: 30px;
    right: 30px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    font-size: 1.2rem;
    font-weight: bold;
    backdrop-filter: blur(10px);
  }
</style>

<div class="public-display">
  {#if lot?.image_url}
    <div class="lot-image">
      <img src="{API_BASE}{lot.image_url}" alt="Lot {lot.LotNumber}" />
    </div>
  {:else}
    <div class="lot-image-placeholder">
      <div class="placeholder-content">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21,15 16,10 5,21"/>
        </svg>
        <p>No image available</p>
      </div>
    </div>
  {/if}
  
  <div class="lot-info">
    <h2>Lot {lot?.LotNumber}: {lot?.StudentName} ({lot?.Department})</h2>
    <div class="bidders-section">
      {#each bidders as bidder}
        <div class="bidder-item">
          {bidder.Identifier}: {bidder.Name}
        </div>
      {/each}
    </div>
  </div>
  
  <div class="clock">{new Date().toLocaleTimeString()}</div>
</div>
