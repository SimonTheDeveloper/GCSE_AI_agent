import React, { useEffect, useState } from 'react';
import { isAuthenticated, beginLogin, beginLogout } from '../auth';
import { useAppStore } from '../store/useAppStore';

export default function RequireAuth({ children }) {
  const { me } = useAppStore();
  const [checking, setChecking] = useState(true);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!isAuthenticated()) {
        const returnTo = window.location.pathname + window.location.search;
        beginLogin(returnTo);
        return;
      }
      try {
        await me();
        if (mounted) setDenied(false);
      } catch (err) {
        const msg = String(err?.message || err || '');
        if (msg.includes(' 403 ') || msg.includes('403')) {
          if (mounted) setDenied(true);
        }
      } finally {
        if (mounted) setChecking(false);
      }
    })();
    return () => { mounted = false; };
  }, [me]);

  if (!isAuthenticated()) return <div className="container py-5">Redirecting to sign in…</div>;
  if (checking) return <div className="container py-5">Checking access…</div>;
  if (denied) {
    return (
      <div className="container py-5">
        <div className="alert alert-warning">
          Your account is not allowed to access this application yet. Please contact the administrator.
        </div>
        <button className="btn btn-outline-secondary" onClick={() => beginLogout()}>Sign out</button>
      </div>
    );
  }
  return children;
}
