<script>
  import { onMount } from 'svelte';
  import MainControl from './MainControl.svelte';
  import SaleList from './SaleList.svelte';
  import BuyerList from './BuyerList.svelte';
  import UserManagement from './UserManagement.svelte';
  import Logging from './Logging.svelte';
  import ThemePicker from './ThemePicker.svelte';
  import { makeAuthenticatedRequest } from '../utils/auth.js';
  import { DEFAULT_THEME } from '../themes.js';

  let lot = {};
  let bidderNumber = '';
  let ws;
  let saleData = [];
  let buyerData = [];
  let bidHistory = [];
  let logMessages = [];
  let currentTab = 'main';
  let theme = DEFAULT_THEME;
  let fairEntrySettings = {};
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  async function fetchSaleData() {
    try {
      const res = await fetch(`${API_BASE}/api/sale`);
      const data = await res.json();
      saleData = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Failed to fetch sale data:', error);
      saleData = [];
    }
  }

  async function fetchBuyerData() {
    try {
      const res = await fetch(`${API_BASE}/api/buyers`);
      const data = await res.json();
      buyerData = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Failed to fetch buyer data:', error);
      buyerData = [];
    }
  }

  async function fetchFairEntrySettings() {
    try {
      const res = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/settings`);
      fairEntrySettings = await res.json();
    } catch (error) {
      console.error('Failed to fetch FairEntry settings:', error);
    }
  }

  async function fetchCurrentState() {
    try {
      const stateRes = await fetch(`${API_BASE}/api/state`);
      const stateData = await stateRes.json();
      if (stateData.lot) {
        lot = stateData.lot;
        if (stateData.bidders && stateData.bidders.length > 0) {
          bidHistory = stateData.bidders.map(bidder => ({
            LotNumber: lot.LotNumber,
            StudentName: lot.StudentName,
            BuyerNumber: bidder.Identifier,
            BuyerName: bidder.Name
          }));
        } else {
          bidHistory = [];
        }
      }
      if (stateData.theme) theme = stateData.theme;
    } catch (error) {
      console.error('Failed to fetch current state:', error);
    }
  }

  onMount(() => {
    const savedLogs = localStorage.getItem('auction-logs');
    if (savedLogs) {
      try {
        logMessages = JSON.parse(savedLogs);
      } catch (e) {
        console.error('Failed to parse saved logs:', e);
        logMessages = [];
      }
    }

    connectWebSocket();

    // Fetch initial data on mount
    fetchSaleData();
    fetchBuyerData();
    fetchCurrentState();
    fetchFairEntrySettings();
  });

  function connectWebSocket() {
    ws = new WebSocket(API_BASE.replace('http', 'ws') + '/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const timestamp = new Date().toLocaleTimeString();
      if (data.type === 'log' && data.message) {
        logMessages = [...logMessages, `${timestamp}: ${data.message}`];
        localStorage.setItem('auction-logs', JSON.stringify(logMessages));
      }

      if (data.lot) {
        lot = data.lot;
        if (data.type === 'state' || data.type === 'bid_update') {
          if (Array.isArray(data.bidders)) {
            bidHistory = data.bidders.map(bidder => ({
              LotNumber: lot.LotNumber,
              StudentName: lot.StudentName,
              BuyerNumber: bidder.Identifier,
              BuyerName: bidder.Name
            }));
          } else {
            bidHistory = [];
          }
        }
      }
      if (data.theme) theme = data.theme;

      if (data.type === 'fairentry_status') {
        const { type, ...rest } = data;
        fairEntrySettings = rest;
      }
      if (data.type === 'buyers_updated') {
        fetchBuyerData();
      }
    };

    // The connection can drop silently (backend restart, network blip, laptop
    // sleep) with no user-visible error - without a reconnect, this screen
    // would keep showing stale lot/bid/FairEntry state indefinitely. Re-fetch
    // everything on reconnect to catch up on whatever was missed while down.
    ws.onclose = () => {
      setTimeout(() => {
        connectWebSocket();
        fetchSaleData();
        fetchBuyerData();
        fetchCurrentState();
        fetchFairEntrySettings();
      }, 2000);
    };
  }

  async function addBidder() {
    if (bidderNumber) {
      try {
        await makeAuthenticatedRequest(`${API_BASE}/api/bidder/add/${bidderNumber}`, { method: 'POST' });
        bidderNumber = '';
      } catch (error) {
        alert('Failed to add bidder: ' + error.message);
      }
    }
  }

  async function nextLot() {
    try {
      await makeAuthenticatedRequest(`${API_BASE}/api/lot/next`, { method: 'POST' });
    } catch (error) {
      alert('Failed to navigate to next lot: ' + error.message);
    }
  }

  async function prevLot() {
    try {
      await makeAuthenticatedRequest(`${API_BASE}/api/lot/prev`, { method: 'POST' });
    } catch (error) {
      alert('Failed to navigate to previous lot: ' + error.message);
    }
  }

  async function handleFileUpload(files, endpoint) {
    try {
      const formData = new FormData();
      formData.append('file', files[0]);
      const response = await makeAuthenticatedRequest(`${API_BASE}${endpoint}`, { 
        method: 'POST', 
        body: formData,
        headers: {} // Don't set Content-Type, let browser set it for FormData
      });
      if (response.ok) {
        alert('Upload complete');
        await fetchSaleData();
        await fetchBuyerData();
        await fetchFairEntrySettings();
      } else {
        const error = await response.json();
        alert(`Upload failed: ${error.detail}`);
      }
    } catch (error) {
      alert('Upload failed: ' + error.message);
    }
  }

  async function handleUndoBidder() {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/bidder/undo`, {
        method: 'POST'
      });
      if (response.ok) {
        const result = await response.json();
        alert(result.message);
      } else {
        const error = await response.json();
        alert(`Undo failed: ${error.detail}`);
      }
    } catch (error) {
      alert('Undo failed: ' + error.message);
    }
  }

  async function handleSaveFairEntrySettings(settings) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/settings`, {
        method: 'POST',
        body: JSON.stringify(settings)
      });
      if (response.ok) {
        fairEntrySettings = await response.json();
      } else {
        const error = await response.json();
        alert(`Failed to save FairEntry settings: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to save FairEntry settings: ' + error.message);
    }
  }

  async function handleToggleFairEntrySync(enabled) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync-toggle`, {
        method: 'POST',
        body: JSON.stringify({ enabled })
      });
      if (response.ok) {
        fairEntrySettings = await response.json();
      } else {
        const error = await response.json();
        alert(`Failed to toggle FairEntry sync: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to toggle FairEntry sync: ' + error.message);
    }
  }

  async function handleSyncFairEntryNow() {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync-now`, {
        method: 'POST'
      });
      const result = await response.json();
      await fetchFairEntrySettings();
      await fetchBuyerData();
      return result;
    } catch (error) {
      return { message: 'Sync failed: ' + error.message };
    }
  }

  async function handleMergeBidders(sourceId, targetId) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/bidder/merge`, {
        method: 'POST',
        body: JSON.stringify({
          source_identifier: sourceId,
          target_identifier: targetId
        })
      });
      if (response.ok) {
        const result = await response.json();
        alert(result.message);
      } else {
        const error = await response.json();
        alert(`Merge failed: ${error.detail}`);
      }
    } catch (error) {
      alert('Merge failed: ' + error.message);
    }
  }
</script>

<style>
  .tab-buttons { margin-bottom: 1rem; }
  .tab-buttons button { 
    margin-right: 0.5rem; 
    padding: 0.5rem 1rem; 
    background: #f8f9fa; 
    border: 1px solid #dee2e6; 
    border-radius: 4px; 
    cursor: pointer; 
  }
  .tab-buttons button.active { 
    background: #007bff; 
    color: white; 
    border-color: #007bff; 
  }
  .tab-buttons button:hover:not(.active) { 
    background: #e9ecef; 
  }
</style>

<div>
  <h2>Admin Console</h2>

  <div class="tab-buttons">
    <button class:active={currentTab === 'main'} on:click={() => currentTab = 'main'}>Main Control</button>
    <button class:active={currentTab === 'sale'} on:click={() => currentTab = 'sale'}>Sale List</button>
    <button class:active={currentTab === 'buyers'} on:click={() => currentTab = 'buyers'}>Buyer List</button>
    <button class:active={currentTab === 'users'} on:click={() => currentTab = 'users'}>User Management</button>
    <button class:active={currentTab === 'preferences'} on:click={() => currentTab = 'preferences'}>Preferences</button>
    <button class:active={currentTab === 'logging'} on:click={() => currentTab = 'logging'}>Logging</button>
  </div>

  {#if currentTab === 'main'}
    <MainControl 
      {lot} 
      bind:bidderNumber 
      {bidHistory}
      onAddBidder={addBidder}
      onNextLot={nextLot}
      onPrevLot={prevLot}
      onUndoBidder={handleUndoBidder}
      onMergeBidders={handleMergeBidders}
    />
  {:else if currentTab === 'sale'}
    <SaleList {saleData} onFileUpload={handleFileUpload} />
  {:else if currentTab === 'buyers'}
    <BuyerList
      {buyerData}
      onFileUpload={handleFileUpload}
      {fairEntrySettings}
      onSaveFairEntrySettings={handleSaveFairEntrySettings}
      onToggleFairEntrySync={handleToggleFairEntrySync}
      onSyncFairEntryNow={handleSyncFairEntryNow}
    />
  {:else if currentTab === 'users'}
    <UserManagement />
  {:else if currentTab === 'preferences'}
    <ThemePicker currentTheme={theme} />
  {:else if currentTab === 'logging'}
    <Logging {logMessages} />
  {/if}
</div>
