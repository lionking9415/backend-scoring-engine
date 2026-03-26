import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AssessmentForm = ({ onComplete }) => {
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  const questionsPerPage = 4; // One subdomain at a time

  useEffect(() => {
    // Fetch questions from backend
    const fetchQuestions = async () => {
      try {
        const response = await axios.get('/api/v1/questions');
        setQuestions(response.data.questions || []);
        setLoading(false);
      } catch (err) {
        // Fallback: use hardcoded questions if backend endpoint doesn't exist
        console.log('Using fallback questions');
        setQuestions(generateFallbackQuestions());
        setLoading(false);
      }
    };
    fetchQuestions();
  }, []);

  const generateFallbackQuestions = () => {
    // Generate 52 questions based on the item dictionary structure
    const subdomains = [
      'Task Initiation', 'Organization', 'Planning', 'Activation',
      'Sustained Attention', 'Task Completion', 'Response Activation',
      'Emotional Regulation', 'Help Seeking', 'Social Engagement',
      'Self Advocacy', 'Follow Through', 'Shutdown Response'
    ];
    
    const questions = [];
    subdomains.forEach((subdomain, idx) => {
      const baseId = idx * 4 + 1;
      questions.push(
        {
          item_id: `Q${String(baseId).padStart(2, '0')}`,
          item_text: `When it's something you LIKE to do (${subdomain}):`,
          response_options: { A: 'Very well', B: 'Well', C: 'Somewhat', D: 'Not well' },
          subdomain: subdomain
        },
        {
          item_id: `Q${String(baseId + 1).padStart(2, '0')}`,
          item_text: `When it's something you do NOT want to do (${subdomain}):`,
          response_options: { A: 'Very well', B: 'Well', C: 'Somewhat', D: 'Not well' },
          subdomain: subdomain
        },
        {
          item_id: `Q${String(baseId + 2).padStart(2, '0')}`,
          item_text: `When facing challenges with ${subdomain.toLowerCase()}:`,
          response_options: { A: 'Adapt easily', B: 'Manage', C: 'Struggle', D: 'Avoid' },
          subdomain: subdomain
        },
        {
          item_id: `Q${String(baseId + 3).padStart(2, '0')}`,
          item_text: `When you have difficulty with ${subdomain.toLowerCase()}, it's usually because:`,
          response_options: { A: 'You want help', B: 'You want something enjoyable', C: 'You want to escape', D: 'You feel overwhelmed' },
          subdomain: subdomain
        }
      );
    });
    return questions;
  };

  const handleResponseChange = (itemId, value) => {
    setResponses(prev => ({
      ...prev,
      [itemId]: value
    }));
  };

  const getCurrentQuestions = () => {
    const start = currentPage * questionsPerPage;
    const end = start + questionsPerPage;
    return questions.slice(start, end);
  };

  const totalPages = Math.ceil(questions.length / questionsPerPage);
  const progress = ((currentPage + 1) / totalPages) * 100;

  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(prev => prev + 1);
      window.scrollTo(0, 0);
    }
  };

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
      window.scrollTo(0, 0);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Convert responses to API format
      const formattedResponses = Object.entries(responses).map(([itemId, letter]) => ({
        item_id: itemId,
        response: { A: 4, B: 3, C: 2, D: 1 }[letter]
      }));

      const payload = {
        user_id: `user_${Date.now()}`,
        report_type: 'STUDENT_SUCCESS',
        responses: formattedResponses,
        demographics: { source: 'web_frontend' },
        include_interpretation: true,
        tier: 'free'
      };

      const response = await axios.post('/api/v1/assess', payload);
      onComplete(response.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit assessment. Please try again.');
      setSubmitting(false);
    }
  };

  const isPageComplete = () => {
    const currentQuestions = getCurrentQuestions();
    return currentQuestions.every(q => responses[q.item_id]);
  };

  const isAssessmentComplete = () => {
    return questions.every(q => responses[q.item_id]);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  const currentQuestions = getCurrentQuestions();
  const currentSubdomain = currentQuestions[0]?.subdomain;

  return (
    <div className="min-h-screen p-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Section {currentPage + 1} of {totalPages}
            </span>
            <span className="text-sm font-medium text-gray-700">
              {Object.keys(responses).length} / {questions.length} answered
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Questions */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-indigo-900 mb-6">
            {currentSubdomain}
          </h2>

          <div className="space-y-8">
            {currentQuestions.map((question, idx) => (
              <div key={question.item_id} className="border-b border-gray-200 pb-6 last:border-b-0">
                <p className="text-lg font-medium text-gray-800 mb-4">
                  {currentPage * questionsPerPage + idx + 1}. {question.item_text}
                </p>
                <div className="space-y-2">
                  {Object.entries(question.response_options).map(([letter, text]) => (
                    <label
                      key={letter}
                      className={`flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        responses[question.item_id] === letter
                          ? 'border-indigo-600 bg-indigo-50'
                          : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name={question.item_id}
                        value={letter}
                        checked={responses[question.item_id] === letter}
                        onChange={(e) => handleResponseChange(question.item_id, e.target.value)}
                        className="w-5 h-5 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-3 text-gray-700">
                        <span className="font-semibold">{letter}.</span> {text}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handlePrevious}
              disabled={currentPage === 0}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                currentPage === 0
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              ← Previous
            </button>

            {currentPage < totalPages - 1 ? (
              <button
                onClick={handleNext}
                disabled={!isPageComplete()}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  isPageComplete()
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                Next →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!isAssessmentComplete() || submitting}
                className={`px-8 py-3 rounded-lg font-medium transition-all ${
                  isAssessmentComplete() && !submitting
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {submitting ? 'Submitting...' : 'Submit Assessment'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentForm;
