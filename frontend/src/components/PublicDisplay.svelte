<script>
    import { onMount } from 'svelte';
    let lot = {};
    let bidders = [];
    let leftColumnBidders = [];
    let rightColumnBidders = [];
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
    const MAX_BIDDERS_PER_COLUMN = 10;

    function distributeBidders(bidderList) {
        if (bidderList.length === 0) {
            leftColumnBidders = [];
            rightColumnBidders = [];
            return;
        }

        if (bidderList.length > MAX_BIDDERS_PER_COLUMN * 2) {
            const startIndex = bidderList.length - (MAX_BIDDERS_PER_COLUMN * 2);
            bidderList = bidderList.slice(startIndex);
        }

        const midPoint = Math.ceil(bidderList.length / 2);
        leftColumnBidders = bidderList.slice(0, midPoint);
        rightColumnBidders = bidderList.slice(midPoint);
    }

    $: distributeBidders(bidders);

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
        
        fetchInitialState();
    });
</script>

<style>
    .container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding: 20px;
        font-family: Arial, sans-serif;
        box-sizing: border-box;
    }
    
    .header {
        text-align: center;
        border: 2px solid black;
        padding: 10px;
        margin-bottom: 20px;
        font-size: 1.5rem;
        font-weight: bold;
        flex-shrink: 0;
    }
    
    .content {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;
    }
    
    .bidders-section {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
    }
    
    .bidders-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 40px;
        flex: 1;
        overflow: hidden;
        min-height: 0;
    }
    
    .bidders-column {
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    
    .bidder-item {
        margin-bottom: 8px;
        font-size: 1.1rem;
        line-height: 1.3;
        word-wrap: break-word;
        text-indent: -2em;
        padding-left: 2em;
        flex-shrink: 0;
    }
    
    .bidder-number {
        display: inline-block;
        min-width: 2em;
        text-indent: 0;
    }
    
    .lot-info {
        border: 2px solid black;
        padding: 10px;
        margin-top: 20px;
        flex-shrink: 0;
    }
    
    .lot-info table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .lot-info th, .lot-info td {
        border: 1px solid black;
        padding: 8px;
        text-align: center;
        font-size: 1.2rem;
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
    
    <div class="content">
        <div class="bidders-section">
            {#if bidders.length > 0}
                <div class="bidders-container">
                    <div class="bidders-column">
                        {#each leftColumnBidders as bidder}
                            <div class="bidder-item">
                                <span class="bidder-number">{bidder.Identifier}</span>	{bidder.Name}
                            </div>
                        {/each}
                    </div>
                    <div class="bidders-column">
                        {#each rightColumnBidders as bidder}
                            <div class="bidder-item">
                                <span class="bidder-number">{bidder.Identifier}</span>	{bidder.Name}
                            </div>
                        {/each}
                    </div>
                </div>
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
                        <td>{lot?.Species || ''}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
