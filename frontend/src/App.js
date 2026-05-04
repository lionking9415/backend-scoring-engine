import React, { useState, useEffect, useCallback } from 'react';
import AssessmentForm from './components/AssessmentForm';
import ScoreCard from './components/ScoreCard';
import DemographicForm from './components/DemographicForm';
import PaymentSuccess from './components/PaymentSuccess';
import Login from './components/Login';
import Signup from './components/Signup';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import ConfirmEmail from './components/ConfirmEmail';
import MyReports from './components/MyReports';
import ReportViewer from './components/ReportViewer';
import CosmicDashboard from './components/CosmicDashboard';
import Account from './components/Account';
import ConsentGate from './legal/ConsentGate';
import LegalFooter from './legal/LegalFooter';
import LegalPage from './legal/LegalPage';
import axios from 'axios';

// =============================================================================
// URL ↔ VIEW ROUTING
// We're a CRA SPA without react-router, so we hand-roll a tiny URL/state sync
// layer using window.history. The goal is: refreshing the browser on any
// report view restores that view (instead of dumping the user back to /).
// Browser back/forward also works because we listen to `popstate`.
//
// URL scheme:
//   /                              → welcome
//   /login                         → login
//   /signup                        → signup
//   /demographics                  → demographics
//   /assessment                    → assessment
//   /my-reports                    → my-reports
//   /report/:id                    → results (ScoreCard)
//   /report/:id/ai                 → ai-reports
//   /report/:id/cosmic             → cosmic-dashboard
//   /success                       → payment-success
// =============================================================================

const VIEW_TO_PATH = {
  welcome: () => '/',
  dashboard: () => '/dashboard',
  account: () => '/account',
  login: () => '/login',
  signup: () => '/signup',
  'forgot-password': () => '/forgot-password',
  'reset-password': () => '/reset-password',
  'confirm-email': () => '/confirm-email',
  demographics: () => '/demographics',
  assessment: () => '/assessment',
  consent: () => '/consent',
  'my-reports': () => '/my-reports',
  results: (id) => (id ? `/report/${encodeURIComponent(id)}` : '/'),
  'ai-reports': (id) =>
    id ? `/report/${encodeURIComponent(id)}/ai` : '/my-reports',
  'cosmic-dashboard': (id) =>
    id ? `/report/${encodeURIComponent(id)}/cosmic` : '/my-reports',
  'payment-success': () => '/success',
  'terms-of-use': () => '/terms-of-use',
  'privacy-policy': () => '/privacy-policy',
  'data-use': () => '/data-use',
};

function parseUrl(pathname) {
  // Returns { view, assessmentId } from a pathname.
  if (!pathname || pathname === '/' || pathname === '') {
    return { view: 'welcome', assessmentId: null };
  }
  const trimmed = pathname.replace(/\/+$/, '');
  if (trimmed === '/dashboard')
    return { view: 'dashboard', assessmentId: null };
  if (trimmed === '/account')
    return { view: 'account', assessmentId: null };
  if (trimmed === '/login') return { view: 'login', assessmentId: null };
  if (trimmed === '/signup') return { view: 'signup', assessmentId: null };
  if (trimmed === '/forgot-password') return { view: 'forgot-password', assessmentId: null };
  if (trimmed === '/reset-password') return { view: 'reset-password', assessmentId: null };
  if (trimmed === '/confirm-email') return { view: 'confirm-email', assessmentId: null };
  if (trimmed === '/demographics')
    return { view: 'demographics', assessmentId: null };
  if (trimmed === '/assessment')
    return { view: 'assessment', assessmentId: null };
  if (trimmed === '/consent')
    return { view: 'consent', assessmentId: null };
  if (trimmed === '/my-reports')
    return { view: 'my-reports', assessmentId: null };
  if (trimmed === '/success')
    return { view: 'payment-success', assessmentId: null };
  if (trimmed === '/terms-of-use')
    return { view: 'terms-of-use', assessmentId: null };
  if (trimmed === '/privacy-policy')
    return { view: 'privacy-policy', assessmentId: null };
  if (trimmed === '/data-use')
    return { view: 'data-use', assessmentId: null };

  const m = trimmed.match(/^\/report\/([^/]+)(\/(ai|cosmic))?$/);
  if (m) {
    const id = decodeURIComponent(m[1]);
    const sub = m[3];
    if (sub === 'ai') return { view: 'ai-reports', assessmentId: id };
    if (sub === 'cosmic')
      return { view: 'cosmic-dashboard', assessmentId: id };
    return { view: 'results', assessmentId: id };
  }
  return { view: 'welcome', assessmentId: null };
}

function buildPath(view, assessmentId) {
  const fn = VIEW_TO_PATH[view];
  return fn ? fn(assessmentId) : '/';
}

// True when the very first paint will need to fetch a report — used to
// pre-arm `loadingReport` and avoid flashing the welcome page for a frame
// before the overlay appears.
function _needsInitialReportFetch() {
  if (typeof window === 'undefined') return false;
  try {
    if (window.localStorage.getItem('best_galaxy_pending_unlock')) return true;
  } catch (e) {
    /* private mode / quota — fall through */
  }
  const path = window.location?.pathname || '';
  // Any URL that is scoped to a specific assessment will need a backend fetch.
  return /^\/(results|ai-reports|cosmic-dashboard|payment-success)(\/|$)/.test(path)
    || path === '/success';
}

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [assessmentData, setAssessmentData] = useState(null);
  const [assessmentId, setAssessmentId] = useState(null);
  const [paidProducts, setPaidProducts] = useState([]);
  const [demographics, setDemographics] = useState(null);
  const [savedResult, setSavedResult] = useState(null);
  const [user, setUser] = useState(null);
  // Lazy initializer: when we already know (from URL or pending-unlock
  // localStorage) that we'll be fetching a report, start in the loading
  // state so the welcome page never gets a chance to flash.
  const [loadingReport, setLoadingReport] = useState(_needsInitialReportFetch);

  // -----------------------------------------------------------------
  // Navigation helper — single entry point for all view changes so the
  // URL stays in sync with state. Replaces raw setCurrentView() calls.
  // -----------------------------------------------------------------
  const pushView = useCallback(
    (view, opts = {}) => {
      const id = opts.assessmentId !== undefined ? opts.assessmentId : assessmentId;
      const url = buildPath(view, id);
      try {
        if (window.location.pathname + window.location.search !== url) {
          if (opts.replace) {
            window.history.replaceState({ view, assessmentId: id }, '', url);
          } else {
            window.history.pushState({ view, assessmentId: id }, '', url);
          }
        }
      } catch (e) {
        // history API unavailable — degrade gracefully (state still updates)
      }
      setCurrentView(view);
    },
    [assessmentId],
  );

  // Re-fetch assessment data from the backend (used on refresh).
  const fetchAssessment = useCallback(
    async (id) => {
      if (!id) return null;
      setLoadingReport(true);
      try {
        const response = await axios.get(`/api/v1/results/${id}`);
        if (response.data?.success) {
          setAssessmentData(response.data.data);
          setAssessmentId(id);
          setPaidProducts(response.data.paid_products || []);
          return response.data;
        }
      } catch (err) {
        console.error('Failed to load report from URL:', err);
      } finally {
        setLoadingReport(false);
      }
      return null;
    },
    [],
  );

  // -----------------------------------------------------------------
  // Mount: restore view + assessment data from URL.
  // Priority order:
  //   1. Stripe success path (already special-cased)
  //   2. Pending-unlock hint from PaymentSuccess
  //   3. Whatever the URL says (this is the refresh-resilience path)
  //   4. Default → welcome
  // -----------------------------------------------------------------
  useEffect(() => {
    // Restore user session
    let restoredEmail = null;
    try {
      const savedUser = localStorage.getItem('best_galaxy_current_user');
      if (savedUser) {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
        restoredEmail = parsed?.email || null;
      }
    } catch (e) {
      /* corrupted */
    }

    // Re-hydrate the cached user from the backend so flags like
    // `has_completed_demographics` (added after first login) get picked up
    // automatically without forcing the user to log out and back in.
    if (restoredEmail) {
      axios
        .get(`/api/v1/auth/user/${encodeURIComponent(restoredEmail)}`)
        .then((response) => {
          const fresh = response?.data?.user;
          if (fresh) {
            setUser((prev) => {
              const merged = { ...(prev || {}), ...fresh };
              try {
                localStorage.setItem(
                  'best_galaxy_current_user',
                  JSON.stringify(merged),
                );
              } catch {/* quota / serialization */}
              return merged;
            });
          }
        })
        .catch(() => {/* offline / 404 — keep cached copy */});
    }

    // Restore "last result" hint (used by the welcome screen's
    // "View My Previous ScoreCard" link — independent of URL routing).
    try {
      const saved = localStorage.getItem('best_galaxy_last_result');
      if (saved) setSavedResult(JSON.parse(saved));
    } catch (e) {
      /* corrupted */
    }

    // Stripe checkout completion always wins.  PaymentSuccess fetches
    // its own data from the `assessment_id` query string, so we clear the
    // app-level loading overlay (it was pre-armed by
    // `_needsInitialReportFetch` for the welcome-flash fix).
    if (window.location.pathname === '/success') {
      setCurrentView('payment-success');
      setLoadingReport(false);
      return;
    }

    // Pending-unlock fast-path (just paid, redirected back to /).
    let pendingHandled = false;
    try {
      const pendingRaw = localStorage.getItem('best_galaxy_pending_unlock');
      if (pendingRaw) {
        const pending = JSON.parse(pendingRaw);
        localStorage.removeItem('best_galaxy_pending_unlock');
        if (pending?.assessment_id) {
          pendingHandled = true;
          setLoadingReport(true);
          axios
            .get(`/api/v1/results/${pending.assessment_id}`)
            .then((response) => {
              if (response.data?.success) {
                setAssessmentData(response.data.data);
                setAssessmentId(pending.assessment_id);
                setPaidProducts(
                  response.data.paid_products || pending.paid_products || [],
                );
                // Use replaceState here so the unlock-redirect URL doesn't
                // clutter the history stack — the user landed on '/'
                // expecting their report, not a back-button-able homepage.
                const url = buildPath('results', pending.assessment_id);
                try {
                  window.history.replaceState(
                    { view: 'results', assessmentId: pending.assessment_id },
                    '',
                    url,
                  );
                } catch (e) {
                  /* ignore */
                }
                setCurrentView('results');
              }
            })
            .catch((err) => {
              console.error('Failed to resume after unlock:', err);
            })
            .finally(() => setLoadingReport(false));
        }
      }
    } catch (e) {
      /* corrupted */
    }

    if (pendingHandled) return;

    // URL-driven restore (refresh case).
    const parsed = parseUrl(window.location.pathname);
    if (parsed.assessmentId) {
      // A report-scoped URL — re-fetch and land the user on the right view.
      const targetView = parsed.view;
      fetchAssessment(parsed.assessmentId).then((res) => {
        if (res?.success) {
          setCurrentView(targetView);
        } else {
          // Couldn't load — drop them to the dashboard.
          try {
            window.history.replaceState({}, '', '/my-reports');
          } catch (e) {}
          setCurrentView('my-reports');
        }
      });
    } else if (parsed.view !== 'welcome') {
      // Logged-out user trying to load /dashboard or /account — send them
      // home.  (handleLogin/handleSignup are responsible for flipping the
      // URL the other way once authenticated.)
      const requiresAuth = parsed.view === 'dashboard' || parsed.view === 'account';
      if (requiresAuth && !restoredEmail) {
        try {
          window.history.replaceState({}, '', '/');
        } catch (e) {/* ignore */}
        setCurrentView('welcome');
      } else {
        setCurrentView(parsed.view);
      }
      // No async fetch happens here, so clear the pre-armed overlay
      // (otherwise users land on a non-report view stuck on "Loading…").
      setLoadingReport(false);
    } else {
      // Plain '/'.  If the user is already authenticated, route them to
      // the focused dashboard instead of the marketing page.
      if (restoredEmail) {
        try {
          window.history.replaceState({}, '', '/dashboard');
        } catch (e) {/* ignore */}
        setCurrentView('dashboard');
      }
      // No async fetch will run; release the overlay either way.
      setLoadingReport(false);
    }
  }, [fetchAssessment]);

  // -----------------------------------------------------------------
  // Browser back/forward — keep view in sync with URL.
  // -----------------------------------------------------------------
  useEffect(() => {
    const onPop = () => {
      const parsed = parseUrl(window.location.pathname);
      // If the URL points at a report we don't have loaded, pull it.
      if (
        parsed.assessmentId &&
        parsed.assessmentId !== assessmentId &&
        ['results', 'ai-reports', 'cosmic-dashboard'].includes(parsed.view)
      ) {
        fetchAssessment(parsed.assessmentId).then((res) => {
          if (res?.success) setCurrentView(parsed.view);
        });
      } else {
        setCurrentView(parsed.view);
      }
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [assessmentId, fetchAssessment]);

  // -----------------------------------------------------------------
  // Handlers — all use pushView() so the URL tracks state.
  // -----------------------------------------------------------------
  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));
    pushView('dashboard');
  };

  // Called by <Account/> after a successful name change.  Merges the fresh
  // user object into state and refreshes the localStorage cache so the
  // dashboard greeting and toolbar show the new name without a full reload.
  const handleAccountUpdated = (freshUser) => {
    if (!freshUser) return;
    setUser((prev) => {
      const merged = { ...(prev || {}), ...freshUser };
      try {
        localStorage.setItem(
          'best_galaxy_current_user',
          JSON.stringify(merged),
        );
      } catch (e) {
        /* quota / serialization */
      }
      return merged;
    });
  };

  const handleSignup = (userData) => {
    setUser(userData);
    setDemographics(userData.demographics);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));

    // If the backend confirms the user already completed the full intake, skip
    // the DemographicForm and go straight to the assessment.  Otherwise,
    // park them on the dashboard so they can review their account before
    // starting the intake/consent flow.
    if (userData?.has_completed_demographics) {
      pushView('assessment');
      return;
    }
    const existingDemo = userData?.demographics || {};
    if (existingDemo.age_range && existingDemo.roles?.length) {
      pushView('assessment');
    } else {
      pushView('dashboard');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('best_galaxy_current_user');
    setAssessmentData(null);
    setAssessmentId(null);
    setDemographics(null);
    pushView('welcome', { assessmentId: null });
  };

  const handleStartAssessment = async () => {
    if (!user) {
      pushView('login');
      return;
    }

    // Pre-assessment consent gate.  If the user hasn't recorded their legal
    // acknowledgement for the current legal version, route them through the
    // consent screen first.  Stored in localStorage AND in the backend
    // (`/api/v1/consent`) so we have an audit trail.
    let consented = false;
    try {
      const raw = localStorage.getItem('best_galaxy_consent');
      if (raw) {
        const c = JSON.parse(raw);
        const { LEGAL_VERSION } = await import('./legal/legalText');
        consented = c?.legal_version === LEGAL_VERSION
          && c?.consents?.terms === true
          && c?.consents?.responsibility === true;
      }
    } catch (_e) {
      /* corrupted localStorage — re-consent */
    }
    if (!consented) {
      pushView('consent');
      return;
    }

    // `has_completed_demographics` is set by the backend when a
    // `demographic_intakes` record exists for this user.
    if (user.has_completed_demographics) {
      setDemographics(user.demographics || {});
      pushView('assessment');
      return;
    }

    // Cached user is stale (e.g. logged in before the flag was added).
    // Do a live check before falling back to the demographic intake form.
    try {
      const response = await axios.get(
        `/api/v1/auth/user/${encodeURIComponent(user.email)}`,
      );
      const fresh = response?.data?.user;
      if (fresh?.has_completed_demographics) {
        const merged = { ...user, ...fresh };
        setUser(merged);
        try {
          localStorage.setItem('best_galaxy_current_user', JSON.stringify(merged));
        } catch {/* quota */}
        setDemographics(fresh.demographics || {});
        pushView('assessment');
        return;
      }
    } catch (_e) {
      /* fall through to local check */
    }

    const existingDemo = user.demographics || {};
    if (existingDemo.age_range && existingDemo.roles?.length) {
      setDemographics(existingDemo);
      pushView('assessment');
    } else {
      pushView('demographics');
    }
  };

  const handleDemographicsComplete = async (demoData) => {
    setDemographics(demoData);
    if (user) {
      const updatedUser = { ...user, demographics: demoData, has_completed_demographics: true };
      setUser(updatedUser);
      localStorage.setItem('best_galaxy_current_user', JSON.stringify(updatedUser));

      const users = JSON.parse(localStorage.getItem('best_galaxy_users') || '{}');
      if (users[user.email]) {
        users[user.email].demographics = demoData;
        localStorage.setItem('best_galaxy_users', JSON.stringify(users));
      }

      try {
        await axios.post('/api/v1/demographics/submit', {
          user_id: user.email,
          responses: demoData,
        });
      } catch (err) {
        console.warn('Demographics backend submit failed (will still proceed):', err);
      }
    }
    pushView('assessment');
  };

  const handleDemographicsSkip = () => {
    setDemographics({ source: 'web_frontend' });
    pushView('assessment');
  };

  // Consent gate handler — fires after the user agrees and the consent
  // has been logged to the backend.  Continues into the same flow as
  // `handleStartAssessment` would have, just past the consent check.
  const handleConsentAgree = () => {
    if (user?.has_completed_demographics) {
      setDemographics(user.demographics || {});
      pushView('assessment');
    } else {
      pushView('demographics');
    }
  };

  const handleAssessmentComplete = (data, resultId) => {
    setAssessmentData(data);
    setAssessmentId(resultId);
    setPaidProducts([]); // a brand-new assessment is always free
    pushView('results', { assessmentId: resultId });

    try {
      localStorage.setItem(
        'best_galaxy_last_result',
        JSON.stringify({ data, resultId, timestamp: new Date().toISOString() }),
      );
    } catch (e) {
      /* storage full */
    }

    if (demographics && user?.email && resultId) {
      axios
        .post('/api/v1/demographics/submit', {
          user_id: user.email,
          assessment_id: resultId,
          responses: demographics,
        })
        .catch(() => {});
    }
  };

  const handleViewSavedResult = async () => {
    if (savedResult) {
      const res = await fetchAssessment(savedResult.resultId);
      if (res?.success) {
        pushView('results', { assessmentId: savedResult.resultId });
      } else {
        alert('Failed to load saved result. Please try again.');
      }
    }
  };

  const handleRestart = () => {
    setAssessmentData(null);
    setAssessmentId(null);
    setPaidProducts([]);
    setDemographics(null);
    pushView('welcome', { assessmentId: null });
  };

  const handleViewReports = () => {
    pushView('my-reports');
  };

  const handleViewReport = async (reportId) => {
    const res = await fetchAssessment(reportId);
    if (res?.success) {
      pushView('results', { assessmentId: reportId });
    } else {
      alert('Failed to load report. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      {currentView === 'login' && (
        <Login
          onLogin={handleLogin}
          onSwitchToSignup={() => pushView('signup')}
          onForgotPassword={() => pushView('forgot-password')}
        />
      )}

      {currentView === 'signup' && (
        <Signup
          onSignup={handleSignup}
          onSwitchToLogin={() => pushView('login')}
        />
      )}

      {currentView === 'forgot-password' && (
        <ForgotPassword
          onSwitchToLogin={() => pushView('login')}
        />
      )}

      {currentView === 'reset-password' && (
        <ResetPassword
          token={new URLSearchParams(window.location.search).get('token')}
          onSwitchToLogin={() => pushView('login')}
        />
      )}

      {currentView === 'confirm-email' && (
        <ConfirmEmail
          token={new URLSearchParams(window.location.search).get('token')}
          onSwitchToLogin={() => pushView('login')}
        />
      )}

      {currentView === 'welcome' && !loadingReport && (
        <>
          {/* ── Visitor top bar (logged-out only — authenticated users
              are redirected to /dashboard on mount). ── */}
          <div className="bg-white/80 backdrop-blur border-b border-gray-200 sticky top-0 z-30">
            <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 flex justify-between items-center gap-2">
              <p className="text-sm font-bold text-indigo-900 tracking-tight truncate min-w-0">
                BEST Galaxy&trade;
              </p>
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => pushView('login')}
                  className="text-xs sm:text-sm text-indigo-700 hover:text-indigo-900 font-semibold px-2 sm:px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  Sign in
                </button>
                <button
                  onClick={() => pushView('signup')}
                  className="text-xs sm:text-sm text-white font-semibold px-3 sm:px-4 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-colors shadow-sm"
                >
                  Get started
                </button>
              </div>
            </div>
          </div>

          {/* ── HERO ── */}
          <section className="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-purple-900 to-indigo-950 text-white">
            <div
              aria-hidden="true"
              className="absolute -top-32 -left-32 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"
            />
            <div
              aria-hidden="true"
              className="absolute -bottom-32 -right-32 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"
            />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16 md:py-20 text-center">
              <span className="inline-block px-3 py-1 mb-5 sm:mb-6 text-[10px] sm:text-xs font-semibold tracking-wider uppercase bg-white/10 border border-white/20 rounded-full text-indigo-100 backdrop-blur">
                BEST Galaxy&trade; Executive Function Assessment
              </span>
              <h1 className="text-3xl sm:text-4xl md:text-6xl font-extrabold leading-tight tracking-tight mb-5 sm:mb-6">
                Map Your Executive
                <span className="block bg-gradient-to-r from-amber-300 via-pink-300 to-purple-300 bg-clip-text text-transparent">
                  Function Galaxy
                </span>
              </h1>
              <p className="text-base sm:text-lg md:text-xl text-indigo-100/90 max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed">
                A research-grounded look at how your internal capacity (BHP) interacts
                with your environmental pressure (PEI) &mdash; across 13 subdomains and four life lenses.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8 sm:mb-10">
                <button
                  onClick={handleStartAssessment}
                  className="w-full sm:w-auto px-6 sm:px-8 py-3.5 sm:py-4 bg-white text-indigo-900 font-bold rounded-xl text-base sm:text-lg shadow-2xl hover:shadow-amber-500/30 hover:-translate-y-0.5 transition-all"
                >
                  Begin Free Assessment &rarr;
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto text-center">
                <div>
                  <div className="text-3xl md:text-4xl font-bold text-amber-300">13</div>
                  <div className="text-[10px] md:text-xs uppercase tracking-wider text-indigo-200/80 mt-1">
                    Subdomains
                  </div>
                </div>
                <div className="border-x border-white/10">
                  <div className="text-3xl md:text-4xl font-bold text-amber-300">4</div>
                  <div className="text-[10px] md:text-xs uppercase tracking-wider text-indigo-200/80 mt-1">
                    Life Lenses
                  </div>
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-bold text-amber-300">10&ndash;15</div>
                  <div className="text-[10px] md:text-xs uppercase tracking-wider text-indigo-200/80 mt-1">
                    Minutes
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ── WHAT YOU GET ── */}
          <section className="bg-gray-50 py-10 sm:py-12 px-4 sm:px-6">
            <div className="max-w-7xl mx-auto">
              <div className="text-center mb-8">
                <p className="text-xs md:text-sm font-semibold uppercase tracking-wider text-indigo-600 mb-2">
                  100% Free ScoreCard
                </p>
                <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">
                  What you&rsquo;ll receive
                </h2>
                <p className="text-gray-600 mt-3 max-w-2xl mx-auto text-sm md:text-base">
                  Every assessment generates a personalized scorecard you can download as a PDF
                  &mdash; no credit card, no tier-gating on the basics.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {[
                  { icon: '\u{1F30C}', title: 'Galaxy Archetype', desc: 'A unique profile name that describes how your executive function operates as a system.' },
                  { icon: '\u2728', title: 'Constellation Map', desc: 'Visualization of all 13 EF subdomain scores, showing where you stabilize and where you bend under load.' },
                  { icon: '\u2696\uFE0F', title: 'Load Balance Indicator', desc: 'See how your internal capacity (BHP) measures against your external pressure (PEI) \u2014 the core of EF load theory.' },
                  { icon: '\u{1F525}', title: 'Strengths & Growth Edges', desc: 'The three areas where you thrive, plus the three growth zones most worth investing in next.' },
                  { icon: '\u{1F52D}', title: '4-Lens Preview', desc: 'A glimpse of how your profile expresses across Personal, Student, Professional, and Family lenses.' },
                  { icon: '\u{1F4C4}', title: 'Downloadable PDF', desc: 'Take your scorecard with you. Reflowed text, accurate progress bars, full disclaimer included.' },
                ].map(({ icon, title, desc }, i) => (
                  <div
                    key={i}
                    className="bg-white rounded-2xl p-6 border border-gray-200 hover:border-indigo-300 hover:shadow-md transition-all"
                  >
                    <div className="text-3xl mb-3" aria-hidden="true">{icon}</div>
                    <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── HOW IT WORKS ── */}
          <section className="bg-white py-10 sm:py-12 px-4 sm:px-6">
            <div className="max-w-6xl mx-auto">
              <div className="text-center mb-8">
                <p className="text-xs md:text-sm font-semibold uppercase tracking-wider text-indigo-600 mb-2">
                  Your Journey
                </p>
                <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">How it works</h2>
              </div>
              <ol className="space-y-5 sm:space-y-6">
                {[
                  { n: '01', title: 'Tell us a little about yourself', desc: 'A short demographic intake helps us interpret your results in context (age range, current role, life stage).' },
                  { n: '02', title: 'Take the BEST Galaxy assessment', desc: 'Questions calibrated by Executive Function Load Theory (PEI \u00d7 BHP). Most people finish in 10\u201315 minutes.' },
                  { n: '03', title: 'Receive your free ScoreCard', desc: 'See your archetype, constellation, load balance, and a preview across four life lenses \u2014 yours to keep.' },
                  { n: '04', title: 'Optionally unlock deeper lenses', desc: 'Personal, Student, Professional, Family lenses unlock contextualized AI narratives. $30 each, or all four as the Cosmic Bundle for $99.99.' },
                ].map((s, i) => (
                  <li key={i} className="flex gap-3 sm:gap-5 items-start">
                    <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white font-bold flex items-center justify-center text-sm sm:text-base">
                      {s.n}
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1">{s.title}</h3>
                      <p className="text-sm text-gray-600 leading-relaxed">{s.desc}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </section>

          {/* ── CLOSING CTA ── */}
          <section className="bg-gradient-to-br from-indigo-50 to-purple-50 py-10 sm:py-12 px-4 sm:px-6">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-indigo-900 mb-4">
                Ready to map your galaxy?
              </h2>
              <p className="text-gray-600 mb-6 sm:mb-8 text-sm sm:text-base">
                The free ScoreCard is yours forever &mdash; no credit card required.
              </p>
              <button
                onClick={handleStartAssessment}
                className="w-full sm:w-auto px-6 sm:px-8 py-3.5 sm:py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold rounded-xl text-base sm:text-lg shadow-lg hover:shadow-xl transition-all"
              >
                Begin Free Assessment
              </button>
              <p className="text-xs text-gray-500 mt-6 italic">
                Educational insights only. Not medical or mental health advice.
              </p>
            </div>
          </section>
        </>
      )}

      {/* ── DASHBOARD (logged-in home / start-assessment screen) ── */}
      {currentView === 'dashboard' && !loadingReport && (
        <>
          {/* Top bar */}
          <div className="bg-white/80 backdrop-blur border-b border-gray-200 sticky top-0 z-30">
            <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 flex justify-between items-center gap-2">
              <div className="min-w-0 flex-1">
                <p className="text-[10px] sm:text-xs text-gray-500 leading-tight">Signed in as</p>
                <p className="text-xs sm:text-sm font-semibold text-indigo-900 leading-tight truncate">
                  {user?.name || user?.email || 'Guest'}
                </p>
              </div>
              <div className="flex gap-1 sm:gap-2 shrink-0">
                <button
                  onClick={handleViewReports}
                  className="text-xs sm:text-sm text-indigo-700 hover:text-indigo-900 font-semibold px-2 sm:px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors whitespace-nowrap"
                >
                  My Reports
                </button>
                <button
                  onClick={handleLogout}
                  className="text-xs sm:text-sm text-gray-600 hover:text-gray-800 font-medium px-2 sm:px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>

          <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 md:py-8">
            {/* Greeting */}
            <header className="mb-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600 mb-1">
                Your Cockpit
              </p>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 leading-tight">
                Welcome back{user?.name ? `, ${String(user.name).split(' ')[0]}` : ''}.
              </h1>
              <p className="text-sm text-gray-600 mt-1 max-w-2xl">
                Start a new assessment or browse the lens reports you&rsquo;ve unlocked.
              </p>
            </header>

            {/* Primary action card — Begin / Continue assessment */}
            <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-700 via-purple-700 to-indigo-900 text-white shadow-xl mb-6">
              <div
                aria-hidden="true"
                className="absolute -top-20 -right-20 w-72 h-72 bg-amber-400/15 rounded-full blur-3xl pointer-events-none"
              />
              <div className="relative p-5 md:p-7 grid md:grid-cols-[1fr_auto] gap-5 md:items-center">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-amber-300 mb-1.5">
                    Free &middot; 10&ndash;15 minutes
                  </p>
                  <h2 className="text-xl md:text-2xl font-bold mb-2 leading-tight">
                    Take the BEST Galaxy&trade; Assessment
                  </h2>
                  <p className="text-sm text-indigo-100/90 leading-relaxed max-w-xl">
                    Your free ScoreCard includes your Galaxy archetype, 13-subdomain
                    constellation, BHP &times; PEI load balance, and a preview across all
                    four life lenses.
                  </p>
                </div>
                <div className="flex flex-col items-stretch md:items-end gap-3">
                  <button
                    onClick={handleStartAssessment}
                    className="px-6 py-3 bg-white text-indigo-900 font-bold rounded-xl text-base shadow-2xl hover:shadow-amber-500/30 hover:-translate-y-0.5 transition-all whitespace-nowrap"
                  >
                    Begin Assessment &rarr;
                  </button>
                </div>
              </div>
            </section>

            {/* Secondary actions grid */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <button
                onClick={handleViewReports}
                className="text-left bg-white border border-gray-200 rounded-2xl p-5 hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="text-2xl mb-2" aria-hidden="true">{'\u{1F4CA}'}</div>
                <h3 className="font-semibold text-gray-900 mb-1">My Reports</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Open your assessment history, download PDFs, and check which lenses
                  you&rsquo;ve unlocked.
                </p>
              </button>

              <button
                onClick={() => pushView('terms-of-use')}
                className="text-left bg-white border border-gray-200 rounded-2xl p-5 hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="text-2xl mb-2" aria-hidden="true">{'\u{1F4DC}'}</div>
                <h3 className="font-semibold text-gray-900 mb-1">Terms &amp; Privacy</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  Read the Terms of Use, Privacy Policy, and Data Use disclosure.
                </p>
              </button>

              <button
                onClick={() => pushView('account')}
                className="text-left bg-white border border-gray-200 rounded-2xl p-5 hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="text-2xl mb-2" aria-hidden="true">{'\u{1F511}'}</div>
                <h3 className="font-semibold text-gray-900 mb-1">Account</h3>
                <p className="text-sm text-gray-600 leading-relaxed break-all">
                  {user?.email || '\u2014'}
                </p>
                <span className="inline-block text-xs font-semibold text-indigo-600 mt-2">
                  Manage name &amp; password &rarr;
                </span>
              </button>
            </section>

            {/* Pricing reminder */}
            <section className="rounded-2xl border border-indigo-100 bg-indigo-50/40 p-5 sm:p-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-indigo-900 mb-1">Unlock deeper lenses</h3>
                  <p className="text-sm text-gray-600 max-w-2xl">
                    After your free ScoreCard, contextualized AI narratives across
                    Personal, Student, Professional, and Family lenses are available
                    individually for <strong>$30</strong>, or all four together as the
                    Cosmic Bundle for <strong>$99.99</strong>.
                  </p>
                </div>
                <span className="text-xs text-gray-500 italic">
                  Educational insights only.
                </span>
              </div>
            </section>
          </main>
        </>
      )}

      {currentView === 'account' && user && (
        <Account
          user={user}
          onUpdated={handleAccountUpdated}
          onBack={() => pushView('dashboard')}
        />
      )}

      {currentView === 'consent' && (
        <ConsentGate
          user={user}
          onAgree={handleConsentAgree}
          onCancel={() => pushView(user ? 'dashboard' : 'welcome')}
          onNavigate={(path) => {
            const parsed = parseUrl(path);
            pushView(parsed.view);
          }}
        />
      )}

      {(currentView === 'terms-of-use'
        || currentView === 'privacy-policy'
        || currentView === 'data-use') && (
        <LegalPage
          slug={currentView}
          onBack={() => pushView(user ? 'dashboard' : 'welcome')}
        />
      )}

      {currentView === 'demographics' && (
        <DemographicForm
          onComplete={handleDemographicsComplete}
          onSkip={handleDemographicsSkip}
        />
      )}

      {currentView === 'assessment' && (
        <AssessmentForm
          onComplete={handleAssessmentComplete}
          demographics={demographics}
          userEmail={user?.email}
        />
      )}

      {currentView === 'results' && (
        <ScoreCard
          data={assessmentData}
          onRestart={handleRestart}
          assessmentId={assessmentId}
          userEmail={user?.email}
          paidProducts={paidProducts}
          onViewCosmic={() => pushView('cosmic-dashboard')}
          onViewAIReports={() => pushView('ai-reports')}
        />
      )}

      {currentView === 'payment-success' && (
        <PaymentSuccess onRestart={handleRestart} />
      )}

      {currentView === 'my-reports' && (
        <MyReports
          userEmail={user?.email}
          onViewReport={handleViewReport}
          onBack={() => pushView(user ? 'dashboard' : 'welcome')}
        />
      )}

      {currentView === 'ai-reports' && (
        <div className="p-4">
          <ReportViewer
            assessmentId={assessmentId}
            userEmail={user?.email}
            paidProducts={paidProducts}
            onBack={() => pushView('results')}
          />
        </div>
      )}

      {currentView === 'cosmic-dashboard' && (
        <div className="p-4">
          <div className="max-w-4xl mx-auto mb-4 flex justify-between items-center">
            <button
              onClick={() => pushView('results')}
              className="text-sm text-indigo-600 hover:text-indigo-800 font-semibold"
            >
              ← Back to ScoreCard
            </button>
          </div>
          <CosmicDashboard
            data={assessmentData}
            apiBase={process.env.REACT_APP_API_URL || ''}
            userId={user?.email || user?.id}
            assessmentId={assessmentId}
            paidProducts={paidProducts}
            onViewReports={() => pushView('ai-reports')}
          />
        </div>
      )}

      {/* Persistent legal footer on every page (skipped during loading
          since the loading overlay covers the screen). */}
      {!loadingReport && (
        <LegalFooter
          onNavigate={(path) => {
            const parsed = parseUrl(path);
            pushView(parsed.view);
          }}
        />
      )}

      {/* Global loading overlay — top-level so it covers every view
          (welcome, my-reports, results-in-flight, etc.) and the welcome
          page never flashes underneath while a fetch is in progress. */}
      {loadingReport && (
        <div className="fixed inset-0 bg-white flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md mx-4">
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mb-4"></div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">Loading Your Report</h3>
              <p className="text-gray-600 text-center">
                Please wait while we retrieve your assessment data...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
