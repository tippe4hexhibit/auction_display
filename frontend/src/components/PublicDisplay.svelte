<script>
  import { onMount } from 'svelte';
  let lot = {};
  let bidders = [];

  onMount(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      lot = data.lot;
      bidders = data.bidders;
    };
  });
</script>

<div style="text-align:center;">
  <h2>Lot {lot?.LotNumber}: {lot?.StudentName} ({lot?.Department})</h2>
  <div style="margin-top:1rem;">
    {#each bidders as bidder}
      <div style="display:inline-block; margin:0.5rem; font-size:1.2rem;">
        {bidder.Identifier}: {bidder.Name}
      </div>
    {/each}
  </div>
  <div style="margin-top:2rem; font-size:1rem;">{new Date().toLocaleTimeString()}</div>
</div>
