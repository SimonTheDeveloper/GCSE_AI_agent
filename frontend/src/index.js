import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { captureTokensFromHash, captureCodeFromQuery } from './auth';

const root = ReactDOM.createRoot(document.getElementById('root'));
function Root() {
  useEffect(() => {
    // Try code flow exchange first; if not code, try implicit hash capture
    (async () => {
      const codeRes = await captureCodeFromQuery();
      if (!codeRes) captureTokensFromHash();
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
