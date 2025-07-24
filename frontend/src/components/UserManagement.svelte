<script>
  import { makeAuthenticatedRequest } from '../utils/auth.js';
  
  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
  
  let users = [];
  let newUsername = '';
  let newPassword = '';
  let changePasswordUsername = '';
  let changePasswordNew = '';
  let loading = false;
  let error = '';
  let success = '';

  async function fetchUsers() {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/users`);
      if (response.ok) {
        users = await response.json();
      } else {
        error = 'Failed to fetch users';
      }
    } catch (err) {
      error = 'Failed to fetch users: ' + err.message;
    }
  }

  async function createUser() {
    if (!newUsername || !newPassword) {
      error = 'Please enter both username and password';
      return;
    }

    loading = true;
    error = '';
    success = '';

    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/users`, {
        method: 'POST',
        body: JSON.stringify({
          username: newUsername,
          password: newPassword
        })
      });

      if (response.ok) {
        success = `User ${newUsername} created successfully`;
        newUsername = '';
        newPassword = '';
        await fetchUsers();
      } else {
        const errorData = await response.json();
        error = errorData.detail || 'Failed to create user';
      }
    } catch (err) {
      error = 'Failed to create user: ' + err.message;
    } finally {
      loading = false;
    }
  }

  async function changePassword() {
    if (!changePasswordUsername || !changePasswordNew) {
      error = 'Please enter both username and new password';
      return;
    }

    loading = true;
    error = '';
    success = '';

    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/users/change-password`, {
        method: 'POST',
        body: JSON.stringify({
          username: changePasswordUsername,
          new_password: changePasswordNew
        })
      });

      if (response.ok) {
        success = `Password changed for ${changePasswordUsername}`;
        changePasswordUsername = '';
        changePasswordNew = '';
      } else {
        const errorData = await response.json();
        error = errorData.detail || 'Failed to change password';
      }
    } catch (err) {
      error = 'Failed to change password: ' + err.message;
    } finally {
      loading = false;
    }
  }

  async function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user ${username}?`)) {
      return;
    }

    loading = true;
    error = '';
    success = '';

    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/api/users/${username}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        success = `User ${username} deleted successfully`;
        await fetchUsers();
      } else {
        const errorData = await response.json();
        error = errorData.detail || 'Failed to delete user';
      }
    } catch (err) {
      error = 'Failed to delete user: ' + err.message;
    } finally {
      loading = false;
    }
  }

  fetchUsers();
</script>

<style>
  .section { margin: 1rem 0; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; }
  .form-group { margin: 0.5rem 0; }
  .form-group label { display: block; margin-bottom: 0.25rem; font-weight: bold; }
  .form-group input { width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
  .btn { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 0.5rem; }
  .btn:hover { background: #0056b3; }
  .btn:disabled { background: #6c757d; cursor: not-allowed; }
  .btn-danger { background: #dc3545; }
  .btn-danger:hover { background: #c82333; }
  .error { color: #dc3545; margin: 0.5rem 0; }
  .success { color: #28a745; margin: 0.5rem 0; }
  .users-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  .users-table th, .users-table td { padding: 0.5rem; border: 1px solid #aaa; text-align: left; }
  .users-table th { background: #f8f9fa; }
</style>

<div>
  <h2>User Management</h2>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if success}
    <div class="success">{success}</div>
  {/if}

  <div class="section">
    <h3>Create New Admin</h3>
    <div class="form-group">
      <label for="new-username">Username:</label>
      <input id="new-username" type="text" bind:value={newUsername} placeholder="Enter username" />
    </div>
    <div class="form-group">
      <label for="new-password">Password:</label>
      <input id="new-password" type="password" bind:value={newPassword} placeholder="Enter password" />
    </div>
    <button class="btn" on:click={createUser} disabled={loading}>
      {loading ? 'Creating...' : 'Create Admin'}
    </button>
  </div>

  <div class="section">
    <h3>Change Password</h3>
    <div class="form-group">
      <label for="change-username">Username:</label>
      <input id="change-username" type="text" bind:value={changePasswordUsername} placeholder="Enter username" />
    </div>
    <div class="form-group">
      <label for="change-password">New Password:</label>
      <input id="change-password" type="password" bind:value={changePasswordNew} placeholder="Enter new password" />
    </div>
    <button class="btn" on:click={changePassword} disabled={loading}>
      {loading ? 'Changing...' : 'Change Password'}
    </button>
  </div>

  <div class="section">
    <h3>Existing Users</h3>
    {#if users.length === 0}
      <p>No users found.</p>
    {:else}
      <table class="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Created At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user}
            <tr>
              <td>{user.username}</td>
              <td>{new Date(user.created_at).toLocaleString()}</td>
              <td>
                {#if user.username !== 'admin'}
                  <button class="btn btn-danger" on:click={() => deleteUser(user.username)} disabled={loading}>
                    Delete
                  </button>
                {:else}
                  <span style="color: #6c757d;">Default Admin</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
