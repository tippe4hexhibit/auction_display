<script>
    import { onMount, tick } from 'svelte';
    import { THEMES, DEFAULT_THEME } from '../themes.js';
    let lot = {};
    let bidders = [];
    let leftColumnBidders = [];
    let rightColumnBidders = [];
    let shouldScroll = false;
    let scrollDuration = 10;
    let viewportEl;
    let innerEl;
    let themeName = DEFAULT_THEME;

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
    // Pixels per second for the scroll; increase to scroll faster
    const SCROLL_SPEED_PX_PER_SEC = 40;

    $: theme = THEMES[themeName] || THEMES[DEFAULT_THEME];

    function distributeBidders(bidderList) {
        if (bidderList.length === 0) {
            leftColumnBidders = [];
            rightColumnBidders = [];
            return;
        }
        const midPoint = Math.ceil(bidderList.length / 2);
        leftColumnBidders = bidderList.slice(0, midPoint);
        rightColumnBidders = bidderList.slice(midPoint);
    }

    $: distributeBidders(bidders);

    async function checkOverflow() {
        await tick();
        if (!viewportEl || !innerEl) return;
        // When scrolling, inner contains the list twice; halve to get true content height.
        const contentHeight = shouldScroll ? innerEl.scrollHeight / 2 : innerEl.scrollHeight;
        const viewportHeight = viewportEl.clientHeight;
        const overflowing = contentHeight > viewportHeight;
        if (overflowing !== shouldScroll) {
            shouldScroll = overflowing;
            // The separator only renders once shouldScroll flips, which changes
            // the measured height; wait for that DOM update before timing it.
            await tick();
        }
        if (shouldScroll) {
            scrollDuration = (innerEl.scrollHeight / 2) / SCROLL_SPEED_PX_PER_SEC;
        }
    }

    $: bidders, checkOverflow();

    async function fetchInitialState() {
        try {
            const stateRes = await fetch(`${API_BASE}/api/state`);
            const stateData = await stateRes.json();
            if (stateData.lot) {
                lot = stateData.lot;
                bidders = stateData.bidders || [];
            }
            if (stateData.theme) themeName = stateData.theme;
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
            if (data.theme) themeName = data.theme;
            // A FairEntry sale sync (background auto-sync or a manual Sync
            // Now) replaces lot data without a lot-navigation event, so it
            // doesn't come with a `lot` field on this message - re-fetch.
            if (data.type === 'sale_updated') fetchInitialState();
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
        background-color: var(--bg, #ffffff);
        color: var(--text, #000000);
    }

    .header {
        text-align: center;
        border: 2px solid var(--border, #000000);
        padding: 10px;
        margin-bottom: 20px;
        font-size: 3rem;
        font-weight: bold;
        flex-shrink: 0;
        background-color: var(--header-bg, #ffffff);
        color: var(--header-text, #000000);
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

    .bidders-viewport {
        flex: 1;
        overflow: hidden;
        min-height: 0;
    }

    .bidders-inner.scrolling {
        animation: scroll-loop var(--scroll-duration, 10s) linear infinite;
    }

    @keyframes scroll-loop {
        0%   { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }

    .scroll-separator {
        margin: 24px 0;
        border-top: 6px solid var(--separator-color, #999999);
    }

    .bidders-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 40px;
    }

    .bidder-item {
        margin-bottom: 8px;
        font-size: 2.53rem;
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
        border: 2px solid var(--border, #000000);
        padding: 10px;
        margin-top: 20px;
        flex-shrink: 0;
    }

    .lot-info table {
        width: 100%;
        border-collapse: collapse;
    }

    .lot-info th, .lot-info td {
        border: 1px solid var(--border, #000000);
        padding: 8px;
        text-align: center;
        font-size: 2.4rem;
    }

    .lot-info th {
        background-color: var(--table-header-bg, #f0f0f0);
        font-weight: bold;
    }
</style>

<div
    class="container"
    style="
        --bg: {theme.background};
        --text: {theme.text};
        --border: {theme.borderColor};
        --header-bg: {theme.headerBg};
        --header-text: {theme.headerText};
        --table-header-bg: {theme.tableHeaderBg};
        --separator-color: {theme.separatorColor};
    "
>
    <div class="header">
        Tippecanoe County 4-H Livestock Auction
    </div>

    <div class="content">
        <div class="bidders-section">
            {#if bidders.length > 0}
                <div class="bidders-viewport" bind:this={viewportEl}>
                    <div
                        class="bidders-inner"
                        class:scrolling={shouldScroll}
                        style="--scroll-duration: {scrollDuration}s"
                        bind:this={innerEl}
                    >
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
                        {#if shouldScroll}
                            <!-- Trailing separator on each copy keeps both loop halves the same
                                 height ([list][separator] x2) so translateY(-50%) wraps seamlessly. -->
                            <div class="scroll-separator" aria-hidden="true"></div>
                            <div class="bidders-container" aria-hidden="true">
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
                            <div class="scroll-separator" aria-hidden="true"></div>
                        {/if}
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
                        <td>{lot?.Department || ''}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
