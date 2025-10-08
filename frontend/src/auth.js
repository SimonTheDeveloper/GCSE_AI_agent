// Minimal Cognito Hosted UI helpers with support for Implicit and Authorization Code (PKCE)

const domain = process.env.REACT_APP_COGNITO_DOMAIN?.replace(/^https?:\/\//, '');
const clientId = process.env.REACT_APP_COGNITO_CLIENT_ID;
const redirectUri = process.env.REACT_APP_COGNITO_REDIRECT_URI || window.location.origin + '/';

function b64urlDecode(s) {
  try {
    const pad = '='.repeat((4 - (s.length % 4)) % 4);
    const base64 = (s + pad).replace(/-/g, '+').replace(/_/g, '/');
    return decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
  } catch { return ''; }
}

export function parseJwt(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(b64urlDecode(payload) || '{}');
  } catch { return null; }
}

export function captureTokensFromHash() {
  if (!window.location.hash) return;
  const qp = new URLSearchParams(window.location.hash.substring(1));
  const at = qp.get('access_token');
  const it = qp.get('id_token');
  const exp = qp.get('expires_in');
  const returnTo = qp.get('state_return_to');
  if (at) localStorage.setItem('access_token', at);
  if (it) localStorage.setItem('id_token', it);
  if (exp) localStorage.setItem('expires_at', String(Date.now() + Number(exp) * 1000));
  window.history.replaceState(null, '', window.location.pathname + window.location.search);
  if (returnTo) {
    try { sessionStorage.setItem('post_auth_return_to', returnTo); } catch {}
  }
}

export async function handleAuthCallbackCode() {
  const qp = new URLSearchParams(window.location.search);
  const code = qp.get('code');
  const returnTo = qp.get('state_return_to');
  if (!code) return false;
  const verifier = sessionStorage.getItem('pkce_verifier') || '';
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: clientId,
    code,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  });
  const resp = await fetch(`https://${domain}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!resp.ok) throw new Error(`Token exchange failed: ${resp.status}`);
  const data = await resp.json();
  if (data.access_token) localStorage.setItem('access_token', data.access_token);
  if (data.id_token) localStorage.setItem('id_token', data.id_token);
  if (data.expires_in) localStorage.setItem('expires_at', String(Date.now() + data.expires_in * 1000));
  window.history.replaceState(null, '', window.location.pathname);
  if (returnTo) {
    try { sessionStorage.setItem('post_auth_return_to', returnTo); } catch {}
  }
  return true;
}

export function getDisplayNameFromTokens() {
  const id = localStorage.getItem('id_token');
  const idc = id ? parseJwt(id) : null;
  const at = localStorage.getItem('access_token');
  const ac = at ? parseJwt(at) : null;
  return (
    idc?.email ||
    idc?.name ||
    idc?.preferred_username ||
    ac?.username ||
    ac?.['cognito:username'] ||
    null
  );
}

export function beginLogout() {
  // Clear locally so UI flips immediately
  localStorage.removeItem('access_token');
  localStorage.removeItem('id_token');
  localStorage.removeItem('expires_at');
  sessionStorage.removeItem('pkce_verifier');
  const logoutUri = process.env.REACT_APP_COGNITO_LOGOUT_URI || redirectUri;
  const url = `https://${domain}/logout?client_id=${encodeURIComponent(clientId)}&logout_uri=${encodeURIComponent(logoutUri)}`;
  window.location.assign(url);
}

// Extra helpers used across the app
export function isAuthenticated() {
  const at = localStorage.getItem('access_token');
  if (!at) return false;
  const expAt = Number(localStorage.getItem('expires_at') || 0);
  if (!expAt) return true; // if unknown, assume valid until API says otherwise
  return Date.now() < expAt - 15_000; // 15s clock skew
}

export function getIdTokenClaims() {
  const it = localStorage.getItem('id_token');
  return it ? parseJwt(it) : null;
}

export function getAccessTokenClaims() {
  const at = localStorage.getItem('access_token');
  return at ? parseJwt(at) : null;
}

export function authHeader() {
  const at = localStorage.getItem('access_token');
  return at ? { Authorization: `Bearer ${at}` } : {};
}

// PKCE utilities
function base64UrlEncode(bytes) {
  return btoa(String.fromCharCode.apply(null, Array.from(bytes)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function sha256(str) {
  const enc = new TextEncoder();
  const data = enc.encode(str);
  const hash = await window.crypto.subtle.digest('SHA-256', data);
  return new Uint8Array(hash);
}

function randomString(length = 43) {
  const bytes = new Uint8Array(length);
  window.crypto.getRandomValues(bytes);
  // map to URL-safe characters
  return base64UrlEncode(bytes).slice(0, length);
}

export function buildAuthorizeUrl() {
  const scope = encodeURIComponent('openid email profile');
  const ru = encodeURIComponent(redirectUri);
  const flow = (process.env.REACT_APP_COGNITO_FLOW || 'code').toLowerCase();
  if (flow === 'implicit') {
    const responseType = encodeURIComponent('token id_token');
    return `https://${domain}/oauth2/authorize?client_id=${encodeURIComponent(clientId)}&redirect_uri=${ru}&response_type=${responseType}&scope=${scope}`;
  }
  // For code flow, we generate PKCE on click, so href is a noop anchor
  return '#';
}

export function buildLogoutUrl() {
  const logoutUri = process.env.REACT_APP_COGNITO_LOGOUT_URI || redirectUri;
  return `https://${domain}/logout?client_id=${encodeURIComponent(clientId)}&logout_uri=${encodeURIComponent(logoutUri)}`;
}

export async function beginLogin(returnTo) {
  const flow = (process.env.REACT_APP_COGNITO_FLOW || 'code').toLowerCase();
  const scope = 'openid email profile';
  const state = randomString(16);
  sessionStorage.setItem('oauth_state', state);
  let stateParams = `state=${encodeURIComponent(state)}`;
  if (returnTo) {
    stateParams += `&state_return_to=${encodeURIComponent(returnTo)}`;
  }

  if (flow === 'implicit') {
    const responseType = 'token id_token';
    const url = `https://${domain}/oauth2/authorize?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=${encodeURIComponent(responseType)}&scope=${encodeURIComponent(scope)}&${stateParams}`;
    window.location.assign(url);
    return;
  }

  // Authorization Code with PKCE
  const verifier = randomString(64);
  const challengeBytes = await sha256(verifier);
  const challenge = base64UrlEncode(challengeBytes);
  sessionStorage.setItem('pkce_verifier', verifier);
  const url = `https://${domain}/oauth2/authorize?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scope)}&${stateParams}&code_challenge_method=S256&code_challenge=${encodeURIComponent(challenge)}`;
  window.location.assign(url);
}
