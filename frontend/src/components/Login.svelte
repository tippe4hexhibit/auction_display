<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
  
  let username = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    if (!username || !password) {
      error = 'Please enter both username and password';
      return;
    }

    loading = true;
    error = '';

    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        dispatch('login-success');
      } else {
        const errorData = await response.json();
        error = errorData.detail || 'Login failed';
      }
    } catch (err) {
      error = 'Network error. Please try again.';
    } finally {
      loading = false;
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      handleLogin();
    }
  }
</script>

<style>
  .login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: #f5f5f5;
  }
  
  .login-form {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
    color: #333;
  }
  
  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    box-sizing: border-box;
  }
  
  input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }
  
  .login-button {
    width: 100%;
    padding: 0.75rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .login-button:hover:not(:disabled) {
    background-color: #0056b3;
  }
  
  .login-button:disabled {
    background-color: #6c757d;
    cursor: not-allowed;
  }
  
  .error {
    color: #dc3545;
    margin-top: 0.5rem;
    font-size: 0.875rem;
  }
  
  .title {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #333;
  }
  
  .default-creds {
    margin-top: 1rem;
    padding: 0.75rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    font-size: 0.875rem;
    color: #6c757d;
  }
</style>

<div class="login-container">
  <div class="login-form">
    <h2 class="title">Admin Login</h2>
    
    <div class="form-group">
      <label for="username">Username:</label>
      <input
        id="username"
        type="text"
        bind:value={username}
        on:keypress={handleKeyPress}
        disabled={loading}
        placeholder="Enter username"
      />
    </div>
    
    <div class="form-group">
      <label for="password">Password:</label>
      <input
        id="password"
        type="password"
        bind:value={password}
        on:keypress={handleKeyPress}
        disabled={loading}
        placeholder="Enter password"
      />
    </div>
    
    <button
      class="login-button"
      on:click={handleLogin}
      disabled={loading}
    >
      {loading ? 'Logging in...' : 'Login'}
    </button>
    
    {#if error}
      <div class="error">{error}</div>
    {/if}
    
    <div class="default-creds">
      <strong>Default credentials:</strong><br>
      Username: admin<br>
      Password: admin123
    </div>
  </div>
</div>
