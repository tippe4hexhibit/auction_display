<script>
    import { onMount } from 'svelte';
    let lot = {};
    let bidders = [];
    let currentBidder = null;
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

    async function fetchInitialState() {
        try {
            const stateRes = await fetch(`${API_BASE}/api/state`);
            const stateData = await stateRes.json();
            if (stateData.lot) {
                lot = stateData.lot;
                bidders = stateData.bidders || [];
                currentBidder = bidders[bidders.length - 1] || null;
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
            if (Array.isArray(data.bidders)) {
                bidders = data.bidders;
                currentBidder = bidders[bidders.length - 1] || null;
            }
        };
        
        // Fetch initial data on mount
        fetchInitialState();
    });
</script>

<div style="text-align:center;">
    {#if currentBidder}
        <h1 style="font-size:5rem;">{currentBidder.Identifier}</h1>
        <h2>{currentBidder.Name}</h2>
    {/if}
    <footer style="margin-top:2rem; font-size:1.5rem;">
        {lot?.LotNumber} - {lot?.StudentName}
    </footer>
</div>
