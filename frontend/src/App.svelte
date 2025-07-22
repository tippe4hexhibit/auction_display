<script>
  import { onMount } from 'svelte';
  import AdminConsole from './components/AdminConsole.svelte';
  import AuctioneerDisplay from './components/AuctioneerDisplay.svelte';
  import PublicDisplay from './components/PublicDisplay.svelte';
  import Login from './components/Login.svelte';
  import { isAuthenticated } from './utils/auth.js';

  let currentPath = '/public';
  let authenticated = false;
  let currentComponent = PublicDisplay;
  
  function getCurrentComponent() {
    switch(currentPath) {
      case '/admin':
        return authenticated ? AdminConsole : Login;
      case '/auctioneer':
        return AuctioneerDisplay;
      case '/public':
        return PublicDisplay;
      default:
        return PublicDisplay;
    }
  }
  
  function updateComponent() {
    currentComponent = getCurrentComponent();
  }
  
  onMount(() => {
    currentPath = window.location.pathname;
    authenticated = isAuthenticated();
    updateComponent();
    
    window.addEventListener('popstate', () => {
      currentPath = window.location.pathname;
      authenticated = isAuthenticated();
      updateComponent();
    });
  });

  function handleLoginSuccess() {
    authenticated = true;
    updateComponent();
  }
</script>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  }
</style>

<main>
  <svelte:component this={currentComponent} on:login-success={handleLoginSuccess} />
</main>
