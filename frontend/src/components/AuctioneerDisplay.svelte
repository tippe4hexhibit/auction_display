<script>
    import { onMount } from 'svelte';
    let lot = {};
    let bidders = [];
    let currentBidder = null;

    onMount(() => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            lot = data.lot;
            bidders = data.bidders;
            currentBidder = bidders[bidders.length - 1] || null;
        };
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