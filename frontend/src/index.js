import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { handleAuthCallbackCode, captureTokensFromHash } from './auth';

const root = ReactDOM.createRoot(document.getElementById('root'));
function Root() {
  useEffect(() => {
    // Try code flow exchange first; if not code, try implicit hash capture
    (async () => {
      try {
        await handleAuthCallbackCode();
      } catch (e) {
        console.warn('Token exchange failed', e);
      } finally {
        captureTokensFromHash();
        // If we have a post-auth return path, navigate there once on boot
        try {
          const returnTo = sessionStorage.getItem('post_auth_return_to');
          if (returnTo) {
            sessionStorage.removeItem('post_auth_return_to');
            if (window.location.pathname + window.location.search !== returnTo) {
              window.history.replaceState(null, '', returnTo);
            }
          }
        } catch {}
        // render after we’ve captured tokens and possibly redirected
      }
    })();
  }, []);
  return (
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

root.render(<Root />);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
