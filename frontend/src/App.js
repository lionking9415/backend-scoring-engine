import React, { useState } from 'react';
import AssessmentForm from './components/AssessmentForm';
import ScoreCard from './components/ScoreCard';

function App() {
  const [currentView, setCurrentView] = useState('welcome');
  const [assessmentData, setAssessmentData] = useState(null);

  const handleStartAssessment = () => {
    setCurrentView('assessment');
  };

  const handleAssessmentComplete = (data) => {
    setAssessmentData(data);
    setCurrentView('results');
  };

  const handleRestart = () => {
    setAssessmentData(null);
    setCurrentView('welcome');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {currentView === 'welcome' && (
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-indigo-900 mb-4">
                BEST Executive Function Galaxy Assessment™
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                A comprehensive assessment of your executive function across 13 key subdomains.
                This assessment takes approximately 10-15 minutes to complete.
              </p>
              <div className="bg-indigo-50 rounded-lg p-6 mb-8">
                <h2 className="text-xl font-semibold text-indigo-900 mb-3">What You'll Discover:</h2>
                <ul className="text-left space-y-2 text-gray-700">
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Your PEI (environmental load) and BHP (internal capacity) scores</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Personalized archetype based on your unique profile</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>Strengths and growth areas across 7 domains</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-indigo-600 mr-2">✓</span>
                    <span>AI-generated interpretation and recommendations</span>
                  </li>
                </ul>
              </div>
              <button
                onClick={handleStartAssessment}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-8 rounded-lg text-lg transition duration-200 shadow-lg hover:shadow-xl"
              >
                Begin Assessment
              </button>
            </div>
          </div>
        </div>
      )}

      {currentView === 'assessment' && (
        <AssessmentForm onComplete={handleAssessmentComplete} />
      )}

      {currentView === 'results' && (
        <ScoreCard data={assessmentData} onRestart={handleRestart} />
      )}
    </div>
  );
}

export default App;
