const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function getAuthToken() {
  return localStorage.getItem('auth_token');
}

export function isAuthenticated() {
  return !!getAuthToken();
}

export function logout() {
  localStorage.removeItem('auth_token');
  window.location.href = '/admin';
}

export function getAuthHeaders() {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function makeAuthenticatedRequest(url, options = {}) {
  const authHeaders = getAuthHeaders();
  
  const headers = options.body instanceof FormData 
    ? { ...authHeaders, ...options.headers }
    : { 'Content-Type': 'application/json', ...authHeaders, ...options.headers };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // The backend silently reissues a fresh token once the current one is
  // past the halfway point of its life, so an actively-used session never
  // hits the hard expiry - only real idle time does.
  const refreshedToken = response.headers.get('X-New-Token');
  if (refreshedToken) {
    localStorage.setItem('auth_token', refreshedToken);
  }

  if (response.status === 401) {
    logout();
    throw new Error('Authentication required');
  }

  return response;
}
