<script>
  import { onMount } from 'svelte';
  import MainControl from './MainControl.svelte';
  import SaleList from './SaleList.svelte';
  import BuyerList from './BuyerList.svelte';
  import { makeAuthenticatedRequest } from '../utils/auth.js';
  
  let lot = {};
  let bidderNumber = '';
  let ws;
  let saleData = [];
  let buyerData = [];
  let bidHistory = [];
  let logMessages = [];
  let currentTab = 'main';
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
        }
      }
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

    ws = new WebSocket(API_BASE.replace('http', 'ws') + '/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const timestamp = new Date().toLocaleTimeString();
      if (data.type === 'log' && data.message) {
        logMessages = [...logMessages, `${timestamp}: ${data.message}`];
        localStorage.setItem('auction-logs', JSON.stringify(logMessages));
      }

      if (data.lot) lot = data.lot;
      if (Array.isArray(data.bidders) && data.bidders.length > 0) {
        bidHistory = [
          ...bidHistory,
          {
            LotNumber: lot.LotNumber,
            StudentName: lot.StudentName,
            BuyerNumber: data.bidders.at(-1)?.Identifier,
            BuyerName: data.bidders.at(-1)?.Name
          }
        ].slice(-10);
        
        setTimeout(() => {
          const tableContainer = document.querySelector('.bidder-table-container');
          if (tableContainer) {
            tableContainer.scrollTop = tableContainer.scrollHeight;
          }
        }, 100);
      }
    };
    
    // Fetch initial data on mount
    fetchSaleData();
    fetchBuyerData();
    fetchCurrentState();
  });

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
  </div>

  {#if currentTab === 'main'}
    <MainControl 
      {lot} 
      bind:bidderNumber 
      {bidHistory} 
      {logMessages}
      onAddBidder={addBidder}
      onNextLot={nextLot}
      onPrevLot={prevLot}
      onUndoBidder={handleUndoBidder}
      onMergeBidders={handleMergeBidders}
    />
  {:else if currentTab === 'sale'}
    <SaleList {saleData} onFileUpload={handleFileUpload} />
  {:else if currentTab === 'buyers'}
    <BuyerList {buyerData} onFileUpload={handleFileUpload} />
  {/if}
</div>
