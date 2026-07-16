<script>
  import { onMount } from 'svelte';
  import MainControl from './MainControl.svelte';
  import SaleList from './SaleList.svelte';
  import BuyerList from './BuyerList.svelte';
  import UserManagement from './UserManagement.svelte';
  import Logging from './Logging.svelte';
  import ThemePicker from './ThemePicker.svelte';
  import FairEntryConnection from './FairEntryConnection.svelte';
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
  let fairEntryConnection = {};
  let buyerSyncStatus = {};
  let saleSyncStatus = {};
  let saleOrderOptions = [];
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

  async function fetchFairEntryConnection() {
    try {
      const res = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/connection`);
      fairEntryConnection = await res.json();
    } catch (error) {
      console.error('Failed to fetch FairEntry connection settings:', error);
    }
  }

  async function fetchBuyerSyncStatus() {
    try {
      const res = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync/buyers`);
      buyerSyncStatus = await res.json();
    } catch (error) {
      console.error('Failed to fetch buyer sync status:', error);
    }
  }

  async function fetchSaleSyncStatus() {
    try {
      const res = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync/sale`);
      saleSyncStatus = await res.json();
    } catch (error) {
      console.error('Failed to fetch sale sync status:', error);
    }
  }

  async function fetchSaleOrderOptions() {
    try {
      const res = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sale-orders`);
      const data = await res.json();
      saleOrderOptions = Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Failed to fetch sale order options:', error);
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
    fetchFairEntryConnection();
    fetchBuyerSyncStatus();
    fetchSaleSyncStatus();
    fetchSaleOrderOptions();
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

      if (data.type === 'fairentry_buyers_sync_status') {
        const { type, ...rest } = data;
        buyerSyncStatus = rest;
      }
      if (data.type === 'fairentry_sale_sync_status') {
        const { type, ...rest } = data;
        saleSyncStatus = rest;
      }
      if (data.type === 'buyers_updated') {
        fetchBuyerData();
      }
      if (data.type === 'sale_updated') {
        fetchSaleData();
        fetchCurrentState();
      }
      if (data.type === 'sale_orders_updated') {
        fetchSaleOrderOptions();
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
        fetchFairEntryConnection();
        fetchBuyerSyncStatus();
        fetchSaleSyncStatus();
        fetchSaleOrderOptions();
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
      // Don't rely solely on the WebSocket broadcast to reflect this: right
      // after login (a fresh mount/reconnect), the socket may not have
      // finished connecting yet, which would silently drop this update.
      await fetchCurrentState();
    } catch (error) {
      alert('Failed to navigate to next lot: ' + error.message);
    }
  }

  async function prevLot() {
    try {
      await makeAuthenticatedRequest(`${API_BASE}/api/lot/prev`, { method: 'POST' });
      await fetchCurrentState();
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
        await fetchBuyerSyncStatus();
        await fetchSaleSyncStatus();
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

  async function handleSaveFairEntryConnection(settings) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/connection`, {
        method: 'POST',
        body: JSON.stringify(settings)
      });
      if (response.ok) {
        fairEntryConnection = await response.json();
      } else {
        const error = await response.json();
        alert(`Failed to save FairEntry connection settings: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to save FairEntry connection settings: ' + error.message);
    }
  }

  async function handleSyncIntervalChange(target, minutes) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync/${target}/interval`, {
        method: 'POST',
        body: JSON.stringify({ sync_interval_minutes: minutes })
      });
      if (response.ok) {
        const status = await response.json();
        if (target === 'buyers') buyerSyncStatus = status;
        else saleSyncStatus = status;
      } else {
        const error = await response.json();
        alert(`Failed to update sync interval: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to update sync interval: ' + error.message);
    }
  }

  async function handleToggleSync(target, enabled) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync/${target}/toggle`, {
        method: 'POST',
        body: JSON.stringify({ enabled })
      });
      if (response.ok) {
        const status = await response.json();
        if (target === 'buyers') buyerSyncStatus = status;
        else saleSyncStatus = status;
      } else {
        const error = await response.json();
        alert(`Failed to toggle sync: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to toggle sync: ' + error.message);
    }
  }

  async function handleSyncNow(target) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sync/${target}/now`, {
        method: 'POST'
      });
      const result = await response.json();
      if (target === 'buyers') {
        await fetchBuyerSyncStatus();
        await fetchBuyerData();
      } else {
        await fetchSaleSyncStatus();
        await fetchSaleData();
        await fetchCurrentState();
      }
      return result;
    } catch (error) {
      return { message: 'Sync failed: ' + error.message };
    }
  }

  async function handleRefreshSaleOrders() {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sale-orders/refresh`, {
        method: 'POST'
      });
      const result = await response.json();
      if (response.ok) {
        saleOrderOptions = Array.isArray(result.options) ? result.options : [];
        await fetchSaleSyncStatus();
      } else {
        alert(`Failed to refresh sale orders: ${result.detail || result.message}`);
      }
    } catch (error) {
      alert('Failed to refresh sale orders: ' + error.message);
    }
  }

  async function handleSelectSaleOrder(saleOrderId) {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/fairentry/sale-orders/select`, {
        method: 'POST',
        body: JSON.stringify({ sale_order_id: saleOrderId })
      });
      if (response.ok) {
        saleSyncStatus = await response.json();
      } else {
        const error = await response.json();
        alert(`Failed to select sale order: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to select sale order: ' + error.message);
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
    <SaleList
      {saleData}
      onFileUpload={handleFileUpload}
      {saleOrderOptions}
      {saleSyncStatus}
      onRefreshSaleOrders={handleRefreshSaleOrders}
      onSelectSaleOrder={handleSelectSaleOrder}
      onSaleSyncIntervalChange={(minutes) => handleSyncIntervalChange('sale', minutes)}
      onToggleSaleSync={(enabled) => handleToggleSync('sale', enabled)}
      onSyncSaleNow={() => handleSyncNow('sale')}
    />
  {:else if currentTab === 'buyers'}
    <BuyerList
      {buyerData}
      onFileUpload={handleFileUpload}
      {buyerSyncStatus}
      onBuyerSyncIntervalChange={(minutes) => handleSyncIntervalChange('buyers', minutes)}
      onToggleBuyerSync={(enabled) => handleToggleSync('buyers', enabled)}
      onSyncBuyersNow={() => handleSyncNow('buyers')}
    />
  {:else if currentTab === 'users'}
    <UserManagement />
  {:else if currentTab === 'preferences'}
    <ThemePicker currentTheme={theme} />
    <FairEntryConnection settings={fairEntryConnection} onSaveSettings={handleSaveFairEntryConnection} />
  {:else if currentTab === 'logging'}
    <Logging {logMessages} />
  {/if}
</div>
