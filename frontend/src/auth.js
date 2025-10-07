// Minimal Cognito Hosted UI helpers with support for Implicit and Authorization Code (PKCE)

const DOMAIN = process.env.REACT_APP_COGNITO_DOMAIN;
const CLIENT_ID = process.env.REACT_APP_COGNITO_CLIENT_ID;
const REDIRECT_URI = process.env.REACT_APP_COGNITO_REDIRECT_URI || window.location.origin + '/';
const LOGOUT_URI = process.env.REACT_APP_COGNITO_LOGOUT_URI || window.location.origin + '/';
const FLOW = (process.env.REACT_APP_COGNITO_FLOW || 'implicit').toLowerCase(); // 'implicit' or 'code'

function base64UrlEncode(buffer) {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function randomString(length = 64) {
  const array = new Uint8Array(length);
  window.crypto.getRandomValues(array);
  return base64UrlEncode(array).substring(0, length);
}

async function sha256(message) {
  const enc = new TextEncoder();
  const data = enc.encode(message);
  return await window.crypto.subtle.digest('SHA-256', data);
}

export function isCodeFlow() {
  return FLOW === 'code';
}

export function buildAuthorizeUrl() {
  if (!DOMAIN || !CLIENT_ID) return '#';
  if (!isCodeFlow()) {
    // Implicit grant
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      response_type: 'token',
      scope: 'openid email profile',
      redirect_uri: REDIRECT_URI,
    });
    return `${DOMAIN}/oauth2/authorize?${params.toString()}`;
  }
  // For code flow, prefer beginLogin() so we can attach PKCE challenge; return fallback URL without challenge.
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    scope: 'openid email profile',
    redirect_uri: REDIRECT_URI,
  });
  return `${DOMAIN}/oauth2/authorize?${params.toString()}`;
}

export async function beginLogin() {
  if (!isCodeFlow()) {
    window.location.href = buildAuthorizeUrl();
    return;
    }
  const verifier = randomString(96);
  const state = randomString(48);
  try { sessionStorage.setItem('pkce_verifier', verifier); } catch {}
  try { sessionStorage.setItem('pkce_state', state); } catch {}
  const challenge = base64UrlEncode(await sha256(verifier));
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    scope: 'openid email profile',
    redirect_uri: REDIRECT_URI,
    code_challenge_method: 'S256',
    code_challenge: challenge,
    state,
  });
  window.location.href = `${DOMAIN}/oauth2/authorize?${params.toString()}`;
}

export function buildLogoutUrl() {
  if (!DOMAIN || !CLIENT_ID) return '#';
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    logout_uri: LOGOUT_URI,
  });
  return `${DOMAIN}/logout?${params.toString()}`;
}

// Parse tokens from location hash after redirect and store them (Implicit)
export function captureTokensFromHash() {
  const hash = window.location.hash || '';
  if (!hash.startsWith('#')) return null;
  const p = new URLSearchParams(hash.substring(1));
  const accessToken = p.get('access_token');
  const idToken = p.get('id_token');
  const expiresIn = p.get('expires_in');
  if (accessToken) {
    try { localStorage.setItem('access_token', accessToken); } catch {}
  }
  if (idToken) {
    try { localStorage.setItem('id_token', idToken); } catch {}
  }
  if (expiresIn) {
    try { localStorage.setItem('token_expires_in', String(expiresIn)); } catch {}
  }
  if (accessToken || idToken) {
    try {
      window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
    } catch {}
  }
  return { accessToken, idToken, expiresIn };
}

// Handle Authorization Code + PKCE exchange on redirect
export async function captureCodeFromQuery() {
  const params = new URLSearchParams(window.location.search || '');
  const code = params.get('code');
  const state = params.get('state');
  if (!code) return null;
  const storedState = (() => { try { return sessionStorage.getItem('pkce_state'); } catch { return null; } })();
  if (storedState && state && storedState !== state) {
    console.warn('PKCE state mismatch');
    return null;
  }
  const codeVerifier = (() => { try { return sessionStorage.getItem('pkce_verifier'); } catch { return null; } })();
  if (!codeVerifier) {
    console.warn('Missing PKCE code verifier');
    return null;
  }
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier,
  });
  const res = await fetch(`${DOMAIN}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!res.ok) {
    const t = await res.text();
    console.error('Token exchange failed:', res.status, t);
    return null;
  }
  const json = await res.json();
  const { access_token, id_token, expires_in } = json;
  if (access_token) {
    try { localStorage.setItem('access_token', access_token); } catch {}
  }
  if (id_token) {
    try { localStorage.setItem('id_token', id_token); } catch {}
  }
  if (expires_in) {
    try { localStorage.setItem('token_expires_in', String(expires_in)); } catch {}
  }
  try {
    sessionStorage.removeItem('pkce_verifier');
    sessionStorage.removeItem('pkce_state');
    // Strip the query params
    window.history.replaceState({}, document.title, window.location.pathname);
  } catch {}
  return { access_token, id_token, expires_in };
}

export function getAccessToken() {
  try { return localStorage.getItem('access_token'); } catch { return null; }
}

export function isAuthenticated() {
  return !!getAccessToken();
}

export function authHeader() {
  const t = getAccessToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}
