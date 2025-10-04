import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';

export default function AppBootstrap({ children }) {
  const { uid, bootstrap, topicsBySubject, fetchSubjects } = useAppStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        if (!uid) {
          await bootstrap('browser-device');
        }
        if (!Object.keys(topicsBySubject || {}).length) {
          await fetchSubjects();
        }
      } catch (_) {
        // ignore for now; UI can still work with limited features
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => { mounted = false; };
  }, [uid, topicsBySubject, bootstrap, fetchSubjects]);

  if (!uid || !ready) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="spinner-border text-primary" role="status" aria-label="Loading" />
        <div style={{ marginTop: 12 }}>Loading…</div>
      </div>
    );
  }
  return children;
}
