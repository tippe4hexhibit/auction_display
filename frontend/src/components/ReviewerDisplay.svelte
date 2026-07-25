<script>
    import { onMount, onDestroy } from 'svelte';
    import { makeAuthenticatedRequest } from '../utils/auth.js';

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

    let lots = [];
    let currentIndex = 0;
    let loading = true;
    let error = '';
    let ws;
    let jumpLotNumber = '';
    let jumpError = '';
    let followLive = false;

    $: currentLot = lots[currentIndex] || null;
    $: if (jumpLotNumber) jumpError = '';

    async function fetchLots() {
        try {
            const res = await makeAuthenticatedRequest(`${API_BASE}/api/review/lots`);
            if (res.ok) {
                lots = await res.json();
                if (currentIndex >= lots.length) currentIndex = Math.max(0, lots.length - 1);
                error = '';
            } else {
                error = 'Failed to load sale data.';
            }
        } catch (err) {
            error = 'Failed to load sale data.';
        } finally {
            loading = false;
        }
    }

    function prevLot() {
        followLive = false;
        if (currentIndex > 0) currentIndex -= 1;
    }

    function nextLot() {
        followLive = false;
        if (currentIndex < lots.length - 1) currentIndex += 1;
    }

    function jumpToLot() {
        const target = jumpLotNumber.trim();
        if (!target) return;

        const index = lots.findIndex((lot) => String(lot.LotNumber).trim() === target);
        if (index === -1) {
            jumpError = `Lot ${target} not found.`;
            return;
        }
        followLive = false;
        currentIndex = index;
        jumpError = '';
        jumpLotNumber = '';
    }

    function handleJumpKeyPress(e) {
        if (e.key === 'Enter') jumpToLot();
    }

    function applyLiveLot(lot) {
        if (!lot) return;
        const index = lots.findIndex((l) => String(l.LotNumber).trim() === String(lot.LotNumber).trim());
        if (index !== -1) currentIndex = index;
    }

    async function syncToLiveLot() {
        try {
            const res = await makeAuthenticatedRequest(`${API_BASE}/api/state`);
            if (res.ok) {
                const data = await res.json();
                applyLiveLot(data.lot);
            }
        } catch (err) {
            // Ignore - the next websocket update will retry.
        }
    }

    function handleFollowLiveChange() {
        if (followLive) syncToLiveLot();
    }

    onMount(() => {
        fetchLots();

        ws = new WebSocket(API_BASE.replace('http', 'ws') + '/ws');
        ws.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'bid_update' || data.type === 'state' || data.type === 'sale_updated') {
                await fetchLots();
            }
            if (followLive && (data.type === 'bid_update' || data.type === 'state')) {
                applyLiveLot(data.lot);
            }
        };
    });

    onDestroy(() => {
        if (ws) ws.close();
    });
</script>

<style>
    .container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        font-family: Arial, sans-serif;
        box-sizing: border-box;
        padding: 1.5rem;
    }

    .header {
        border: 2px solid black;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        background-color: white;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .nav-button {
        padding: 0.75rem 1.25rem;
        font-size: 1.1rem;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    .nav-button:hover:not(:disabled) {
        background: #0056b3;
    }

    .nav-button:disabled {
        background: #6c757d;
        cursor: not-allowed;
    }

    .lot-summary {
        flex: 1;
        text-align: center;
    }

    .lot-title {
        font-size: 1.6rem;
        font-weight: bold;
    }

    .lot-subtitle {
        font-size: 1.1rem;
        color: #444;
        margin-top: 0.25rem;
    }

    .lot-position {
        font-size: 0.95rem;
        color: #777;
        margin-top: 0.25rem;
    }

    .buyers-section {
        flex: 1;
        margin-top: 1.5rem;
        border: 2px solid black;
        border-radius: 8px;
        background: white;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .buyers-list {
        overflow-y: auto;
        flex: 1;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th, td {
        border: 1px solid #ccc;
        padding: 0.75rem 1rem;
        text-align: left;
        font-size: 1.1rem;
    }

    th {
        background: #f0f0f0;
        position: sticky;
        top: 0;
    }

    .empty-message {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-style: italic;
        color: #777;
    }

    .status-message {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        color: #777;
    }

    .jump-section {
        margin-top: 1.5rem;
        border: 2px solid black;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        background-color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .jump-controls {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .jump-section label {
        font-size: 1.1rem;
        font-weight: bold;
    }

    .jump-section input {
        padding: 0.6rem;
        font-size: 1.1rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        width: 140px;
    }

    .jump-error {
        color: #dc3545;
        font-size: 0.95rem;
    }

    .follow-live-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        white-space: nowrap;
    }

    .follow-live-toggle input {
        width: 1.2rem;
        height: 1.2rem;
        cursor: pointer;
    }
</style>

<div class="container">
    <div class="header">
        <button class="nav-button" on:click={prevLot} disabled={currentIndex <= 0}>&larr; Previous</button>
        <div class="lot-summary">
            {#if currentLot}
                <div class="lot-title">Lot {currentLot.LotNumber} &mdash; {currentLot.StudentName}</div>
                <div class="lot-subtitle">{currentLot.Department}</div>
                <div class="lot-position">Lot {currentIndex + 1} of {lots.length}</div>
            {:else if !loading}
                <div class="lot-title">No lots available</div>
            {/if}
        </div>
        <button class="nav-button" on:click={nextLot} disabled={currentIndex >= lots.length - 1}>Next &rarr;</button>
    </div>

    <div class="buyers-section">
        {#if loading}
            <div class="status-message">Loading sale data&hellip;</div>
        {:else if error}
            <div class="status-message">{error}</div>
        {:else if !currentLot || (currentLot.Bidders || []).length === 0}
            <div class="empty-message">No buyers recorded for this lot yet.</div>
        {:else}
            <div class="buyers-list">
                <table>
                    <thead>
                        <tr><th>Buyer #</th><th>Buyer Name</th></tr>
                    </thead>
                    <tbody>
                        {#each currentLot.Bidders as buyer}
                            <tr><td>{buyer.Identifier}</td><td>{buyer.Name}</td></tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    </div>

    <div class="jump-section">
        <div class="jump-controls">
            <label for="jump-lot-number">Jump to Lot #:</label>
            <input
                id="jump-lot-number"
                type="text"
                bind:value={jumpLotNumber}
                on:keypress={handleJumpKeyPress}
                placeholder="Lot number"
            />
            <button class="nav-button" on:click={jumpToLot}>Go</button>
            {#if jumpError}
                <span class="jump-error">{jumpError}</span>
            {/if}
        </div>
        <label class="follow-live-toggle">
            <input type="checkbox" bind:checked={followLive} on:change={handleFollowLiveChange} />
            Follow the auction display live
        </label>
    </div>
</div>
