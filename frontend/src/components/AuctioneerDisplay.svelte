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

<style>
    .container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        font-family: Arial, sans-serif;
    }
    
    .header {
        text-align: center;
        border: 2px solid black;
        padding: 15px;
        margin: 20px;
        font-size: 1.8rem;
        font-weight: bold;
        background-color: white;
    }
    
    .main-display {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 40px;
    }
    
    .bidder-number {
        font-size: 8rem;
        font-weight: bold;
        margin-bottom: 20px;
        color: #000;
    }
    
    .bidder-name {
        font-size: 3rem;
        margin-bottom: 40px;
        color: #000;
    }
    
    .lot-info {
        border: 2px solid black;
        margin: 20px;
        background-color: white;
    }
    
    .lot-info table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .lot-info th, .lot-info td {
        border: 1px solid black;
        padding: 15px;
        text-align: center;
        font-size: 1.5rem;
    }
    
    .lot-info th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
</style>

<div class="container">
    <div class="header">
        Tippecanoe County 4-H Livestock Auction
    </div>
    
    <div class="main-display">
        {#if currentBidder}
            <div class="bidder-number">{currentBidder.Identifier}</div>
            <div class="bidder-name">{currentBidder.Name}</div>
        {:else}
            <div class="bidder-number">-</div>
            <div class="bidder-name">No Current Bidder</div>
        {/if}
    </div>
    
    <div class="lot-info">
        <table>
            <thead>
                <tr>
                    <th>Lot #</th>
                    <th>Exhibitor</th>
                    <th>Species</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{lot?.LotNumber || ''}</td>
                    <td>{lot?.StudentName || ''}</td>
                    <td>{lot?.Department || ''}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
