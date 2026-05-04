import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AssessmentForm = ({ onComplete, demographics, userEmail }) => {
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [animating, setAnimating] = useState(false);
  const [slideDir, setSlideDir] = useState('right');

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await axios.get('/api/v1/questions');
        setQuestions(response.data.questions || []);
        setLoading(false);
      } catch (err) {
        console.log('Using fallback questions');
        setQuestions(generateFallbackQuestions());
        setLoading(false);
      }
    };
    fetchQuestions();
  }, []);

  const generateFallbackQuestions = () => {
    const subdomains = [
      'Task Initiation', 'Organization', 'Planning', 'Activation',
      'Sustained Attention', 'Task Completion', 'Response Activation',
      'Emotional Regulation', 'Help Seeking', 'Social Engagement',
      'Self Advocacy', 'Follow Through', 'Shutdown Response'
    ];
    const qs = [];
    subdomains.forEach((subdomain, idx) => {
      const baseId = idx * 4 + 1;
      qs.push(
        { item_id: `Q${String(baseId).padStart(2, '0')}`, item_text: `When it's something you LIKE to do (${subdomain}):`, response_options: { A: 'Very well', B: 'Well', C: 'Somewhat', D: 'Not well' }, subdomain },
        { item_id: `Q${String(baseId + 1).padStart(2, '0')}`, item_text: `When it's something you do NOT want to do (${subdomain}):`, response_options: { A: 'Very well', B: 'Well', C: 'Somewhat', D: 'Not well' }, subdomain },
        { item_id: `Q${String(baseId + 2).padStart(2, '0')}`, item_text: `When facing challenges with ${subdomain.toLowerCase()}:`, response_options: { A: 'Adapt easily', B: 'Manage', C: 'Struggle', D: 'Avoid' }, subdomain },
        { item_id: `Q${String(baseId + 3).padStart(2, '0')}`, item_text: `When you have difficulty with ${subdomain.toLowerCase()}, it's usually because:`, response_options: { A: 'You want help', B: 'You want something enjoyable', C: 'You want to escape', D: 'You feel overwhelmed' }, subdomain }
      );
    });
    return qs;
  };

  const totalQuestions = questions.length;
  const progress = totalQuestions > 0 ? ((currentIndex + 1) / totalQuestions) * 100 : 0;
  const answeredCount = Object.keys(responses).length;
  const currentQ = questions[currentIndex];

  const goTo = useCallback((nextIndex, dir) => {
    if (animating) return;
    setSlideDir(dir);
    setAnimating(true);
    setTimeout(() => {
      setCurrentIndex(nextIndex);
      setAnimating(false);
    }, 200);
  }, [animating]);

  const handleSelect = (letter) => {
    setResponses(prev => ({ ...prev, [currentQ.item_id]: letter }));

    // Auto-advance after short delay
    if (currentIndex < totalQuestions - 1) {
      setTimeout(() => goTo(currentIndex + 1, 'right'), 350);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) goTo(currentIndex - 1, 'left');
  };

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) goTo(currentIndex + 1, 'right');
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const formattedResponses = Object.entries(responses).map(([itemId, letter]) => ({
        item_id: itemId,
        response: { A: 4, B: 3, C: 2, D: 1 }[letter]
      }));

      const payload = {
        user_id: userEmail || `user_${Date.now()}`,
        user_email: userEmail,
        // The assessment itself is *lens-neutral* — the same raw
        // responses & scoring data apply to every lens. The user's
        // lens choice lives in their PURCHASES (`paid_products`) and
        // their generated AI Narrative reports, NOT on the assessment
        // row. The backend still requires this field to be one of
        // REPORT_LENSES, so we send the most generic lens as a
        // placeholder. Display surfaces (e.g. MyReports) must read
        // `paid_products`, not this field.
        report_type: 'PERSONAL_LIFESTYLE',
        responses: formattedResponses,
        demographics: demographics || { source: 'web_frontend' },
        include_interpretation: true,
        tier: 'free'
      };

      const response = await axios.post('/api/v1/assess', payload);
      onComplete(response.data.data, response.data.result_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit. Please try again.');
      setSubmitting(false);
    }
  };

  const isComplete = answeredCount >= totalQuestions;

  // Colour for each option (teeter-totter: green → yellow → orange → red)
  const optionStyles = {
    A: { bg: 'bg-emerald-50', border: 'border-emerald-400', activeBg: 'bg-emerald-500', text: 'text-emerald-700', activeText: 'text-white', icon: '🟢' },
    B: { bg: 'bg-sky-50', border: 'border-sky-400', activeBg: 'bg-sky-500', text: 'text-sky-700', activeText: 'text-white', icon: '🔵' },
    C: { bg: 'bg-amber-50', border: 'border-amber-400', activeBg: 'bg-amber-500', text: 'text-amber-700', activeText: 'text-white', icon: '🟡' },
    D: { bg: 'bg-rose-50', border: 'border-rose-400', activeBg: 'bg-rose-500', text: 'text-rose-700', activeText: 'text-white', icon: '🔴' },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Preparing your assessment...</p>
        </div>
      </div>
    );
  }

  if (!currentQ) return null;

  const selected = responses[currentQ.item_id];

  return (
    <div className="min-h-screen flex flex-col px-3 py-4 sm:p-4">

      {/* ── TOP BAR: visual progress ── */}
      <div className="max-w-2xl w-full mx-auto mb-4">
        {/* Star field progress dots */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-indigo-400 tracking-widest uppercase">
            {currentQ.subdomain}
          </span>
          <span className="text-xs font-semibold text-gray-500">
            {currentIndex + 1} / {totalQuestions}
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Milestone markers */}
        <div className="flex justify-between mt-1">
          {[0, 25, 50, 75, 100].map(pct => (
            <div key={pct} className={`w-2 h-2 rounded-full transition-colors ${progress >= pct ? 'bg-indigo-500' : 'bg-gray-300'}`} />
          ))}
        </div>
      </div>

      {/* ── QUESTION CARD ── */}
      <div className="flex-1 flex items-center justify-center">
        <div className={`max-w-2xl w-full transition-all duration-200 ${animating ? (slideDir === 'right' ? 'opacity-0 translate-x-8' : 'opacity-0 -translate-x-8') : 'opacity-100 translate-x-0'}`}>
          <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8 md:p-10">

            {/* Question text */}
            <p className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-800 text-center leading-relaxed mb-6 sm:mb-8">
              {currentQ.item_text}
            </p>

            {/* ── Visual scale options ── */}
            <div className="space-y-3">
              {Object.entries(currentQ.response_options).map(([letter, text]) => {
                const isSelected = selected === letter;
                const s = optionStyles[letter];

                return (
                  <button
                    key={letter}
                    onClick={() => handleSelect(letter)}
                    className={`w-full flex items-center p-3 sm:p-4 md:p-5 rounded-xl border-2 transition-all duration-200 transform
                      ${isSelected
                        ? `${s.activeBg} ${s.activeText} border-transparent shadow-lg scale-[1.02]`
                        : `${s.bg} ${s.text} ${s.border} hover:shadow-md hover:scale-[1.01]`
                      }`}
                  >
                    {/* Visual indicator dot */}
                    <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-base sm:text-lg font-bold shrink-0 transition-colors
                      ${isSelected ? 'bg-white/30' : 'bg-white'}`}>
                      {isSelected ? '✓' : letter}
                    </div>

                    <span className="ml-3 sm:ml-4 text-left font-medium text-sm sm:text-base md:text-lg">
                      {text}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* ── Teeter-totter visual scale ── */}
            <div className="mt-6 px-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-600">Strong</span>
                <div className="flex-1 mx-3 h-3 bg-gray-100 rounded-full relative overflow-hidden">
                  {selected && (
                    <div
                      className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ${
                        selected === 'A' ? 'w-full bg-gradient-to-r from-emerald-400 to-emerald-500' :
                        selected === 'B' ? 'w-3/4 bg-gradient-to-r from-sky-400 to-sky-500' :
                        selected === 'C' ? 'w-1/2 bg-gradient-to-r from-amber-400 to-amber-500' :
                        'w-1/4 bg-gradient-to-r from-rose-400 to-rose-500'
                      }`}
                    />
                  )}
                  {!selected && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-[10px] text-gray-400">Select above</span>
                    </div>
                  )}
                </div>
                <span className="text-xs font-semibold text-rose-500">Needs Growth</span>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm text-center">
                {error}
              </div>
            )}
          </div>

          {/* ── NAVIGATION ── */}
          <div className="flex justify-between items-center mt-6 gap-2">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className={`px-3 sm:px-5 py-2.5 sm:py-3 rounded-xl text-sm sm:text-base font-semibold transition-all ${
                currentIndex === 0
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-white hover:shadow-md'
              }`}
            >
              ← Back
            </button>

            <div className="flex items-center space-x-1 shrink-0">
              {/* Quick jump dots for current subdomain (4 questions) */}
              {(() => {
                const subdomainStart = Math.floor(currentIndex / 4) * 4;
                return [0, 1, 2, 3].map(offset => {
                  const idx = subdomainStart + offset;
                  if (idx >= totalQuestions) return null;
                  const q = questions[idx];
                  const isAnswered = q && responses[q.item_id];
                  const isCurrent = idx === currentIndex;
                  return (
                    <button
                      key={idx}
                      onClick={() => goTo(idx, idx > currentIndex ? 'right' : 'left')}
                      className={`w-3 h-3 rounded-full transition-all ${
                        isCurrent ? 'bg-indigo-600 scale-125' :
                        isAnswered ? 'bg-indigo-300' : 'bg-gray-300'
                      }`}
                    />
                  );
                });
              })()}
            </div>

            {currentIndex < totalQuestions - 1 ? (
              <button
                onClick={handleNext}
                disabled={!selected}
                className={`px-3 sm:px-5 py-2.5 sm:py-3 rounded-xl text-sm sm:text-base font-semibold transition-all ${
                  selected
                    ? 'text-indigo-600 hover:bg-white hover:shadow-md'
                    : 'text-gray-300 cursor-not-allowed'
                }`}
              >
                Skip →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!isComplete || submitting}
                className={`px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-sm sm:text-base font-bold transition-all ${
                  isComplete && !submitting
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg hover:shadow-xl'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {submitting ? (
                  <span className="flex items-center space-x-2">
                    <span className="animate-spin">⏳</span>
                    <span>Processing...</span>
                  </span>
                ) : (
                  `See My Results ✨`
                )}
              </button>
            )}
          </div>

          {/* Answered counter */}
          <div className="text-center mt-4">
            <span className="text-xs text-gray-400">
              {answeredCount} of {totalQuestions} answered
              {isComplete && !submitting && currentIndex < totalQuestions - 1 &&
                ' — You can submit anytime!'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentForm;
