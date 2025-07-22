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
  
  
  .lot-info {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 40px;
    border-radius: 12px;
    text-align: center;
    backdrop-filter: blur(10px);
    min-width: 600px;
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
