import React, { useState, useEffect } from 'react';
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

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [assessmentData, setAssessmentData] = useState(null);
  const [assessmentId, setAssessmentId] = useState(null);
  const [paidProducts, setPaidProducts] = useState([]);
  const [demographics, setDemographics] = useState(null);
  const [savedResult, setSavedResult] = useState(null);
  const [user, setUser] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  // Check URL path, user session, and localStorage on mount
  useEffect(() => {
    // Check if we're on the success page
    const path = window.location.pathname;
    if (path === '/success') {
      setCurrentView('payment-success');
      return;
    }

    // Check for existing user session
    try {
      const savedUser = localStorage.getItem('best_galaxy_current_user');
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
    } catch (e) {
      // Ignore corrupted data
    }

    // Check localStorage for previous results
    try {
      const saved = localStorage.getItem('best_galaxy_last_result');
      if (saved) {
        const parsed = JSON.parse(saved);
        setSavedResult(parsed);
      }
    } catch (e) {
      // Ignore corrupted data
    }

    // After a Stripe checkout, PaymentSuccess persists a "pending unlock"
    // hint. When the user lands back on '/', auto-route them into the
    // ScoreCard for that assessment so the freshly-unlocked Cosmic
    // Dashboard / AI Reports buttons are immediately reachable.
    try {
      const pendingRaw = localStorage.getItem('best_galaxy_pending_unlock');
      if (pendingRaw) {
        const pending = JSON.parse(pendingRaw);
        localStorage.removeItem('best_galaxy_pending_unlock');
        if (pending?.assessment_id) {
          setLoadingReport(true);
          axios.get(`/api/v1/results/${pending.assessment_id}`)
            .then((response) => {
              if (response.data?.success) {
                setAssessmentData(response.data.data);
                setAssessmentId(pending.assessment_id);
                setPaidProducts(response.data.paid_products || pending.paid_products || []);
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
      // Ignore corrupted data
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));
    setCurrentView('welcome');
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
      setCurrentView('assessment');
    } else {
      setCurrentView('demographics');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('best_galaxy_current_user');
    setAssessmentData(null);
    setAssessmentId(null);
    setDemographics(null);
    setCurrentView('welcome');
  };

  const handleStartAssessment = () => {
    if (!user) {
      setCurrentView('login');
      return;
    }
    // Check if user has completed the full demographic intake (has age_range from the 16-question form)
    const existingDemo = user.demographics || {};
    if (existingDemo.age_range && existingDemo.roles) {
      // Already completed full intake — proceed directly
      setDemographics(existingDemo);
      setCurrentView('assessment');
    } else {
      // Route through full demographic intake
      setCurrentView('demographics');
    }
  };

  const handleDemographicsComplete = async (demoData) => {
    setDemographics(demoData);
    // Update user demographics in localStorage
    if (user) {
      const updatedUser = { ...user, demographics: demoData };
      setUser(updatedUser);
      localStorage.setItem('best_galaxy_current_user', JSON.stringify(updatedUser));
      
      // Also update in users database
      const users = JSON.parse(localStorage.getItem('best_galaxy_users') || '{}');
      if (users[user.email]) {
        users[user.email].demographics = demoData;
        localStorage.setItem('best_galaxy_users', JSON.stringify(users));
      }

      // Submit to backend so report generator can auto-fetch demographics
      try {
        await axios.post('/api/v1/demographics/submit', {
          user_id: user.email,
          responses: demoData,
        });
      } catch (err) {
        console.warn('Demographics backend submit failed (will still proceed):', err);
      }
    }
    setCurrentView('assessment');
  };

  const handleDemographicsSkip = () => {
    setDemographics({ source: 'web_frontend' });
    setCurrentView('assessment');
  };

  const handleAssessmentComplete = (data, resultId) => {
    setAssessmentData(data);
    setAssessmentId(resultId);
    setPaidProducts([]); // a brand-new assessment is always free
    setCurrentView('results');

    // Persist to localStorage
    try {
      localStorage.setItem('best_galaxy_last_result', JSON.stringify({
        data,
        resultId,
        timestamp: new Date().toISOString(),
      }));
    } catch (e) {
      // Storage full or unavailable
    }

    // Re-submit demographics keyed to the assessment_id so report generator can find them
    if (demographics && user?.email && resultId) {
      axios.post('/api/v1/demographics/submit', {
        user_id: user.email,
        assessment_id: resultId,
        responses: demographics,
      }).catch(() => {});
    }
  };

  const handleViewSavedResult = async () => {
    if (savedResult) {
      setLoadingReport(true);
      try {
        // Always re-fetch from backend so the server can decide free vs paid
        // and return the correct projection.
        const response = await axios.get(`/api/v1/results/${savedResult.resultId}`);
        if (response.data.success) {
          setAssessmentData(response.data.data);
          setAssessmentId(savedResult.resultId);
          setPaidProducts(response.data.paid_products || []);
          setCurrentView('results');
        }
      } catch (err) {
        console.error('Failed to load saved result:', err);
        alert('Failed to load saved result. Please try again.');
      } finally {
        setLoadingReport(false);
      }
    }
  };

  const handleRestart = () => {
    setAssessmentData(null);
    setAssessmentId(null);
    setPaidProducts([]);
    setDemographics(null);
    setCurrentView('welcome');
  };

  const handleViewReports = () => {
    setCurrentView('my-reports');
  };

  const handleViewReport = async (reportId) => {
    setLoadingReport(true);
    try {
      // Backend decides whether to return the free ScoreCard projection or
      // the full paid result and which SKUs are unlocked.
      const response = await axios.get(`/api/v1/results/${reportId}`);
      if (response.data.success) {
        setAssessmentData(response.data.data);
        setAssessmentId(reportId);
        setPaidProducts(response.data.paid_products || []);
        setCurrentView('results');
      }
    } catch (err) {
      console.error('Failed to load report:', err);
      alert('Failed to load report. Please try again.');
    } finally {
      setLoadingReport(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {currentView === 'login' && (
        <Login 
          onLogin={handleLogin} 
          onSwitchToSignup={() => setCurrentView('signup')} 
        />
      )}

      {currentView === 'signup' && (
        <Signup 
          onSignup={handleSignup} 
          onSwitchToLogin={() => setCurrentView('login')} 
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
                  <p className="text-lg font-semibold text-indigo-900">{user.name || user.email}</p>
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
                <h2 className="text-xl font-semibold text-indigo-900 mb-3">Your Free ScoreCard Includes:</h2>
                <ul className="text-left space-y-2 text-gray-700">
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Your unique executive function <strong>Archetype</strong></span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Executive function <strong>constellation</strong> visualization</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span><strong>Load Balance</strong> indicator (PEI × BHP)</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Top <strong>strengths</strong> and <strong>growth edges</strong></span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Preview across <strong>4 life lenses</strong> (Personal, Student, Professional, Family)</span>
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
                  <p className="text-gray-600 text-center">Please wait while we retrieve your assessment data...</p>
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
          onViewCosmic={() => setCurrentView('cosmic-dashboard')}
          onViewAIReports={() => setCurrentView('ai-reports')}
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
            onBack={() => setCurrentView('welcome')}
          />
          {loadingReport && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-md mx-4">
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mb-4"></div>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">Loading Your Report</h3>
                  <p className="text-gray-600 text-center">Please wait while we retrieve your assessment data...</p>
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
            onBack={() => setCurrentView('results')}
          />
        </div>
      )}

      {currentView === 'cosmic-dashboard' && (
        <div className="p-4">
          <div className="max-w-4xl mx-auto mb-4 flex justify-between items-center">
            <button
              onClick={() => setCurrentView('results')}
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
            onViewReports={() => setCurrentView('ai-reports')}
          />
        </div>
      )}

    </div>
  );
}

export default App;
