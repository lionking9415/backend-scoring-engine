import React, { useState, useEffect, useCallback } from 'react';
import AssessmentForm from './components/AssessmentForm';
import ScoreCard from './components/ScoreCard';
import DemographicForm from './components/DemographicForm';
import PaymentSuccess from './components/PaymentSuccess';
import Login from './components/Login';
import Signup from './components/Signup';
import MyReports from './components/MyReports';
import ReportViewer from './components/ReportViewer';
import CosmicDashboard from './components/CosmicDashboard';
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
  login: () => '/login',
  signup: () => '/signup',
  demographics: () => '/demographics',
  assessment: () => '/assessment',
  'my-reports': () => '/my-reports',
  results: (id) => (id ? `/report/${encodeURIComponent(id)}` : '/'),
  'ai-reports': (id) =>
    id ? `/report/${encodeURIComponent(id)}/ai` : '/my-reports',
  'cosmic-dashboard': (id) =>
    id ? `/report/${encodeURIComponent(id)}/cosmic` : '/my-reports',
  'payment-success': () => '/success',
};

function parseUrl(pathname) {
  // Returns { view, assessmentId } from a pathname.
  if (!pathname || pathname === '/' || pathname === '') {
    return { view: 'welcome', assessmentId: null };
  }
  const trimmed = pathname.replace(/\/+$/, '');
  if (trimmed === '/login') return { view: 'login', assessmentId: null };
  if (trimmed === '/signup') return { view: 'signup', assessmentId: null };
  if (trimmed === '/demographics')
    return { view: 'demographics', assessmentId: null };
  if (trimmed === '/assessment')
    return { view: 'assessment', assessmentId: null };
  if (trimmed === '/my-reports')
    return { view: 'my-reports', assessmentId: null };
  if (trimmed === '/success')
    return { view: 'payment-success', assessmentId: null };

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

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [assessmentData, setAssessmentData] = useState(null);
  const [assessmentId, setAssessmentId] = useState(null);
  const [paidProducts, setPaidProducts] = useState([]);
  const [demographics, setDemographics] = useState(null);
  const [savedResult, setSavedResult] = useState(null);
  const [user, setUser] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

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
    try {
      const savedUser = localStorage.getItem('best_galaxy_current_user');
      if (savedUser) setUser(JSON.parse(savedUser));
    } catch (e) {
      /* corrupted */
    }

    // Restore "last result" hint (used by the welcome screen's
    // "View My Previous ScoreCard" link — independent of URL routing).
    try {
      const saved = localStorage.getItem('best_galaxy_last_result');
      if (saved) setSavedResult(JSON.parse(saved));
    } catch (e) {
      /* corrupted */
    }

    // Stripe checkout completion always wins.
    if (window.location.pathname === '/success') {
      setCurrentView('payment-success');
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
      setCurrentView(parsed.view);
    }
    // Otherwise we stay on default 'welcome'.
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
    pushView('welcome');
  };

  const handleSignup = (userData) => {
    setUser(userData);
    setDemographics(userData.demographics);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));

    // Full demographic intake (16-question form) is required before assessment.
    // The signup form only collects 4 quick fields, so unless the user
    // already has the full intake (`age_range` + `roles`), route them to
    // the demographics view.
    const existingDemo = userData?.demographics || {};
    if (existingDemo.age_range && existingDemo.roles) {
      pushView('assessment');
    } else {
      pushView('demographics');
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

  const handleStartAssessment = () => {
    if (!user) {
      pushView('login');
      return;
    }
    const existingDemo = user.demographics || {};
    if (existingDemo.age_range && existingDemo.roles) {
      setDemographics(existingDemo);
      pushView('assessment');
    } else {
      pushView('demographics');
    }
  };

  const handleDemographicsComplete = async (demoData) => {
    setDemographics(demoData);
    if (user) {
      const updatedUser = { ...user, demographics: demoData };
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {currentView === 'login' && (
        <Login
          onLogin={handleLogin}
          onSwitchToSignup={() => pushView('signup')}
        />
      )}

      {currentView === 'signup' && (
        <Signup
          onSignup={handleSignup}
          onSwitchToLogin={() => pushView('login')}
        />
      )}

      {currentView === 'welcome' && (
        <>
          <div className="flex items-center justify-center min-h-screen p-4">
            <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
              {user && (
                <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-sm text-gray-500">Welcome back,</p>
                    <p className="text-lg font-semibold text-indigo-900">
                      {user.name || user.email}
                    </p>
                  </div>
                  <div className="flex gap-4">
                    <button
                      onClick={handleViewReports}
                      className="text-sm text-indigo-600 hover:text-indigo-800 font-semibold transition-colors"
                    >
                      📊 My Reports
                    </button>
                    <button
                      onClick={handleLogout}
                      className="text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
              <div className="text-center">
                <h1 className="text-4xl font-bold text-indigo-900 mb-4">
                  BEST Executive Function Galaxy Assessment™
                </h1>
                <p className="text-lg text-gray-600 mb-8">
                  Discover your executive function profile across 13 subdomains.
                  Takes approximately 10–15 minutes. <strong>100% Free.</strong>
                </p>
                <div className="bg-indigo-50 rounded-xl p-6 mb-8">
                  <h2 className="text-xl font-semibold text-indigo-900 mb-3">
                    Your Free ScoreCard Includes:
                  </h2>
                  <ul className="text-left space-y-2 text-gray-700">
                    <li className="flex items-start">
                      <span className="text-indigo-600 mr-2">✓</span>
                      <span>
                        Your unique executive function <strong>Archetype</strong>
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-indigo-600 mr-2">✓</span>
                      <span>
                        Executive function <strong>constellation</strong> visualization
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-indigo-600 mr-2">✓</span>
                      <span>
                        <strong>Load Balance</strong> indicator (PEI × BHP)
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-indigo-600 mr-2">✓</span>
                      <span>
                        Top <strong>strengths</strong> and <strong>growth edges</strong>
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-indigo-600 mr-2">✓</span>
                      <span>
                        Preview across <strong>4 life lenses</strong> (Personal,
                        Student, Professional, Family)
                      </span>
                    </li>
                  </ul>
                </div>

                <button
                  onClick={handleStartAssessment}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-4 px-10 rounded-xl text-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  Begin Free Assessment
                </button>

                {savedResult && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-gray-500 text-sm mb-3">
                      You have a previous result from{' '}
                      {new Date(savedResult.timestamp).toLocaleDateString()}
                    </p>
                    <button
                      onClick={handleViewSavedResult}
                      className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm underline transition-colors"
                    >
                      View My Previous ScoreCard
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
          {loadingReport && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-md mx-4">
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
        </>
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
        <>
          <MyReports
            userEmail={user?.email}
            onViewReport={handleViewReport}
            onBack={() => pushView('welcome')}
          />
          {loadingReport && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-md mx-4">
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
        </>
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
    </div>
  );
}

export default App;
