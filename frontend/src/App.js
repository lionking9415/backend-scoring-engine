import React, { useState, useEffect } from 'react';
import AssessmentForm from './components/AssessmentForm';
import ScoreCard from './components/ScoreCard';
import DemographicForm from './components/DemographicForm';
import PaymentSuccess from './components/PaymentSuccess';
import Login from './components/Login';
import Signup from './components/Signup';

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [assessmentData, setAssessmentData] = useState(null);
  const [assessmentId, setAssessmentId] = useState(null);
  const [demographics, setDemographics] = useState(null);
  const [savedResult, setSavedResult] = useState(null);
  const [user, setUser] = useState(null);

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
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));
    setCurrentView('welcome');
  };

  const handleSignup = (userData) => {
    setUser(userData);
    localStorage.setItem('best_galaxy_current_user', JSON.stringify(userData));
    setCurrentView('demographics');
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
    setCurrentView('demographics');
  };

  const handleDemographicsComplete = (demoData) => {
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
  };

  const handleViewSavedResult = () => {
    if (savedResult) {
      setAssessmentData(savedResult.data);
      setAssessmentId(savedResult.resultId);
      setCurrentView('results');
    }
  };

  const handleRestart = () => {
    setAssessmentData(null);
    setAssessmentId(null);
    setDemographics(null);
    setCurrentView('welcome');
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
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
            {user && (
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
                <div>
                  <p className="text-sm text-gray-500">Welcome back,</p>
                  <p className="text-lg font-semibold text-indigo-900">{user.name || user.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
                >
                  Logout
                </button>
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
        />
      )}

      {currentView === 'payment-success' && (
        <PaymentSuccess onRestart={handleRestart} />
      )}
    </div>
  );
}

export default App;
