import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { isAuthenticated, beginLogout, getDisplayNameFromTokens, buildAuthorizeUrl, buildLogoutUrl, beginLogin, getIdTokenClaims, getAccessTokenClaims } from '../auth';
import { useAppStore } from '../store/useAppStore';

export default function LayoutSite({ children, showTopStrip = false }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [displayName, setDisplayName] = useState(getDisplayNameFromTokens());
  const [signedIn, setSignedIn] = useState(isAuthenticated());
  const [open, setOpen] = useState(false);
  const isActive = (pathPrefix) => location.pathname === pathPrefix || location.pathname.startsWith(pathPrefix + '/');

  useEffect(() => {
    // Close mobile menu on route change
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onStorage = () => {
      setSignedIn(isAuthenticated());
      setDisplayName(getDisplayNameFromTokens());
    };
    window.addEventListener('storage', onStorage);
    // also refresh after mount
    onStorage();
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const onSignOut = (e) => {
    e.preventDefault();
    beginLogout();
  };

  const signInUrl = buildAuthorizeUrl();
  const signOutUrl = buildLogoutUrl();

  // Fetch user claims when signed in
  const { me } = useAppStore();
  const [claims, setClaims] = useState(null);
  const [loadingClaims, setLoadingClaims] = useState(false);

  const displayNameFunc = (c) => {
    if (!c) return 'Account';
    return c.email || c.name || c.preferred_username || c.username || c['cognito:username'] || 'Account';
  };
  const nameLabel = claims ? displayNameFunc(claims) : (displayName || 'Account');
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!signedIn) { setClaims(null); return; }
      // Optimistic local claims (UI-only) from ID/access tokens
      const localId = getIdTokenClaims();
      const localAt = getAccessTokenClaims();
      if (localId || localAt) {
        const displayOnly = localId || localAt;
        if (mounted) setClaims(prev => prev || displayOnly);
      }
      setLoadingClaims(true);
      try {
        const res = await me();
        if (mounted) setClaims(res?.claims || null);
      } catch (e) {
        // If token invalid/expired, clear UI (user can sign in again)
        if (mounted) setClaims(null);
      } finally {
        if (mounted) setLoadingClaims(false);
      }
    })();
    return () => { mounted = false; };
  }, [signedIn, me]);

  // Replace the non-clickable # with a real button
  return (
    <div className="main-wrapper d-flex flex-column" style={{minHeight: '100vh'}}>
      {/* Header Section Start (with top strip) */}
      <div className="header-section">
        {/* Header Top (toggle via prop) */}
        {showTopStrip && (
          <div className="header-top d-none d-lg-block">
            <div className="container">
              <div className="header-top-wrapper">
                <div className="header-top-left">
                  <p>All course 28% off for <Link to="/">Liberian people’s.</Link></p>
                </div>
                <div className="header-top-medal">
                  <div className="top-info">
                    <p><i className="flaticon-phone-call"></i> <a href="tel:9702621413">(970) 262-1413</a></p>
                    <p><i className="flaticon-email"></i> <a href="mailto:address@gmail.com">address@gmail.com</a></p>
                  </div>
                </div>
                <div className="header-top-right">
                  <ul className="social">
                    <li><a href="https://facebook.com" target="_blank" rel="noreferrer"><i className="flaticon-facebook"></i></a></li>
                    <li><a href="https://twitter.com" target="_blank" rel="noreferrer"><i className="flaticon-twitter"></i></a></li>
                    <li><a href="https://skype.com" target="_blank" rel="noreferrer"><i className="flaticon-skype"></i></a></li>
                    <li><a href="https://instagram.com" target="_blank" rel="noreferrer"><i className="flaticon-instagram"></i></a></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Header Main */}
        <div className="header-main">
          <div className="container">
            <div className="header-main-wrapper">
              {/* Logo placeholder (none for now) */}
              <div className="header-logo">
                <Link to="/">GCSE</Link>
              </div>

              {/* Menu (use theme nav items; map to SPA routes where relevant) */}
              <div className="header-menu d-none d-lg-block">
                <ul className="nav-menu">
                  <li className={isActive('/') ? 'active' : ''}><Link to="/">Home</Link></li>
                  <li className={isActive('/subjects') ? 'active' : ''}>
                    <Link to="/subjects">Subjects</Link>
                    <ul className="sub-menu">
                      <li><Link to="/subjects/maths">Maths</Link></li>
                      <li><Link to="/subjects/science">Science</Link></li>
                    </ul>
                  </li>
                  <li className={isActive('/review') ? 'active' : ''}><Link to="/review">Review</Link></li>
                  <li className={isActive('/homework') ? 'active' : ''}><Link to="/homework">My homework</Link></li>
                </ul>
              </div>

              {/* Auth controls */}
              <div className="header-sign-in-up d-none d-lg-block">
                <ul>
                  {!signedIn ? (
                    <li><a className="sign-in" href={signInUrl} onClick={(e) => { e.preventDefault(); beginLogin(); }}>Sign In</a></li>
                  ) : claims ? (
                    <li className="position-relative">
                      <a href="#" onClick={(e) => e.preventDefault()} className="sign-in">
                        {nameLabel}
                        <i className="icofont-rounded-down ms-1" aria-hidden="true"></i>
                      </a>
                      <ul className="sub-menu" style={{ right: 0 }}>
                        <li><span className="dropdown-item-text text-muted" style={{ padding: '8px 16px', display: 'block' }}>{nameLabel}</span></li>
                        <li><hr className="dropdown-divider" /></li>
                        <li><a className="sign-in" href={signOutUrl} onClick={(e) => { e.preventDefault(); beginLogout(); }}>Sign Out</a></li>
                      </ul>
                    </li>
                  ) : (
                    <>
                      <li><span className="text-muted" style={{ padding: '8px 12px', display: 'inline-block' }}>{loadingClaims ? 'Loading…' : nameLabel}</span></li>
                      <li><a className="sign-in" href={signOutUrl} onClick={(e) => { e.preventDefault(); beginLogout(); }}>Sign Out</a></li>
                    </>
                  )}
                </ul>
              </div>

              {/* Mobile toggle (visual only; js handled by theme main.js if needed) */}
              <div className="header-toggle d-lg-none">
                <button type="button" className="menu-toggle btn p-0 border-0 bg-transparent" onClick={() => setMobileOpen(true)}>
                  <span></span>
                  <span></span>
                  <span></span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Menu (static structure for now) */}
      <div className={`mobile-menu ${mobileOpen ? 'open' : ''}`}>
        <button type="button" className="menu-close btn p-0 border-0 bg-transparent" onClick={() => setMobileOpen(false)}><i className="icofont-close-line"></i></button>
        <div className="mobile-top">
          <p><i className="flaticon-phone-call"></i> <a href="tel:9702621413">(970) 262-1413</a></p>
          <p><i className="flaticon-email"></i> <a href="mailto:address@gmail.com">address@gmail.com</a></p>
        </div>
        <div className="mobile-menu-items">
          <ul className="nav-menu">
            <li className={isActive('/') ? 'active' : ''}><Link to="/" onClick={() => setMobileOpen(false)}>Home</Link></li>
            <li className={isActive('/subjects') ? 'active' : ''}><Link to="/subjects" onClick={() => setMobileOpen(false)}>Subjects</Link></li>
            <li className={isActive('/review') ? 'active' : ''}><Link to="/review" onClick={() => setMobileOpen(false)}>Review</Link></li>
            <li className={isActive('/homework') ? 'active' : ''}><Link to="/homework" onClick={() => setMobileOpen(false)}>My homework</Link></li>
            <li className={isActive('/subjects/maths') ? 'active' : ''}><Link to="/subjects/maths" onClick={() => setMobileOpen(false)}>Maths</Link></li>
            <li className={isActive('/subjects/science') ? 'active' : ''}><Link to="/subjects/science" onClick={() => setMobileOpen(false)}>Science</Link></li>
            <li><a href="/theme/edule/contact.html" onClick={() => setMobileOpen(false)}>Contact</a></li>
            {!signedIn ? (
              <li><a className="sign-in" href={signInUrl} onClick={(e) => { e.preventDefault(); setMobileOpen(false); beginLogin(); }}>Sign In</a></li>
            ) : (
              <>
                <li className="text-muted" style={{ padding: '8px 12px' }}>{displayName}</li>
                <li><a className="sign-in" href={signOutUrl} onClick={(e) => { e.preventDefault(); setMobileOpen(false); beginLogout(); }}>Sign Out</a></li>
              </>
            )}
          </ul>
        </div>
      </div>
  {/* Overlay for mobile menu (used by theme JS) */}
  <div className={`overlay ${mobileOpen ? 'open' : ''}`} onClick={() => setMobileOpen(false)} />

      {/* Page content */}
      <main style={{flex: 1}}>
        {children}
      </main>

      {/* Footer (minimal) */}
      <div className="section footer-section mt-auto">
        <div className="footer-copyright">
          <div className="container">
            <div className="row align-items-center">
              <div className="col-md-6">
                <div className="copyright-text">
                  <p>© 2025 <span>Study with Seb</span> Made by Kamia Consulting</p>
                </div>
              </div>
              <div className="col-md-6">
                <div className="copyright-text">
                  <p><a href="/theme/edule/contact.html" onClick={() => setMobileOpen(false)}>Contact</a></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
