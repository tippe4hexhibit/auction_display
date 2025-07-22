<script>
  import AdminConsole from './components/AdminConsole.svelte';
  import AuctioneerDisplay from './components/AuctioneerDisplay.svelte';
  import PublicDisplay from './components/PublicDisplay.svelte';
  import Login from './components/Login.svelte';
  import { isAuthenticated } from './utils/auth.js';

  let currentPath = window.location.pathname;
  let authenticated = isAuthenticated();
  
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
  
  let currentComponent = getCurrentComponent();
  
  // Listen for navigation changes
  window.addEventListener('popstate', () => {
    currentPath = window.location.pathname;
    authenticated = isAuthenticated();
    currentComponent = getCurrentComponent();
  });

  function handleLoginSuccess() {
    authenticated = true;
    currentComponent = getCurrentComponent();
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
