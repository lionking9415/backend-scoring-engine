import React from 'react';
import LockedSections from './LockedSections';

const ScoreCard = ({ data, onRestart, assessmentId, userEmail }) => {
  const [upgradingFromLens, setUpgradingFromLens] = React.useState(false);
  const [downloadingPdf, setDownloadingPdf] = React.useState(false);
  const [pdfError, setPdfError] = React.useState(null);

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  const {
    galaxy_snapshot,
    constellation,
    load_balance,
    strengths,
    growth_edges,
    lens_teasers,
    locked_features,
    metadata,
  } = data;

  const handleDownloadPdf = async () => {
    if (!assessmentId) {
      setPdfError('No assessment ID available');
      console.error('PDF Download Error: No assessment ID');
      return;
    }

    setDownloadingPdf(true);
    setPdfError(null);
    console.log('Starting PDF download for assessment ID:', assessmentId);

    try {
      const axios = (await import('axios')).default;
      console.log('Requesting PDF from:', `/api/v1/export/scorecard-pdf/${assessmentId}`);
      
      const response = await axios.get(`/api/v1/export/scorecard-pdf/${assessmentId}`, {
        responseType: 'blob',
        timeout: 30000, // 30 second timeout
      });

      console.log('PDF response received, size:', response.data.size, 'bytes');
      console.log('Response headers:', response.headers);

      // Create blob and download
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `BEST_Galaxy_ScoreCard_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('PDF download initiated successfully');
      setDownloadingPdf(false);
    } catch (err) {
      console.error('PDF Download Error:', err);
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      
      let errorMessage = 'Failed to download PDF';
      if (err.response) {
        errorMessage = `Server error (${err.response.status}): ${err.response.data?.detail || err.response.statusText}`;
      } else if (err.request) {
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        errorMessage = err.message;
      }
      
      setPdfError(errorMessage);
      setDownloadingPdf(false);
    }
  };

  const handleLensUpgrade = async () => {
    if (!assessmentId) {
      alert('No assessment ID available');
      return;
    }

    if (!userEmail) {
      alert('Please log in to unlock the full report');
      return;
    }

    setUpgradingFromLens(true);

    try {
      const axios = (await import('axios')).default;
      const response = await axios.post('/api/v1/payment/create-checkout', null, {
        params: {
          assessment_id: assessmentId,
          customer_email: userEmail,
          success_url: `${window.location.origin}/success?assessment_id=${assessmentId}`,
          cancel_url: window.location.href
        }
      });

      if (response.data.success && response.data.session) {
        if (response.data.session.checkout_url) {
          window.location.href = response.data.session.checkout_url;
        } else if (response.data.session.error) {
          alert(response.data.session.error);
          setUpgradingFromLens(false);
        }
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create checkout session');
      setUpgradingFromLens(false);
    }
  };

  const getLoadColor = (status) => {
    if (status === 'Balanced') return 'text-green-600 bg-green-50 border-green-200';
    if (status === 'Slightly Imbalanced') return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getLoadIcon = (status) => {
    if (status === 'Balanced') return '⚖️';
    if (status === 'Slightly Imbalanced') return '⚠️';
    return '🔴';
  };

  const getBarColor = (pct) => {
    if (pct >= 75) return 'bg-green-500';
    if (pct >= 50) return 'bg-blue-500';
    if (pct >= 35) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const lensIcons = {
    PERSONAL_LIFESTYLE: '🌟',
    STUDENT_SUCCESS: '🎓',
    PROFESSIONAL_LEADERSHIP: '💼',
    FAMILY_ECOSYSTEM: '👨‍👩‍👧‍👦',
  };

  return (
    <div className="min-h-screen p-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── 1. GALAXY SNAPSHOT HEADER ── */}
        <div className="bg-gradient-to-br from-indigo-700 via-purple-700 to-indigo-900 rounded-2xl shadow-xl p-8 text-white text-center">
          <p className="text-indigo-200 text-sm uppercase tracking-widest mb-2">You are</p>
          <h1 className="text-4xl font-extrabold mb-3">
            {galaxy_snapshot?.archetype_name || 'Unknown'}
          </h1>
          <p className="text-lg text-indigo-100 italic">
            "{galaxy_snapshot?.tagline}"
          </p>
        </div>

        {/* ── 2. EF CONSTELLATION SCORECARD ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">
            Your Executive Function Constellation
          </h2>
          <div className="space-y-4">
            {constellation?.map((group, idx) => (
              <div key={idx}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-gray-700">{group.name}</span>
                  <span className="text-sm font-semibold text-gray-500">{group.percentage}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-700 ${getBarColor(group.percentage)}`}
                    style={{ width: `${group.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── 3. LOAD BALANCE SNAPSHOT ── */}
        <div className={`rounded-2xl shadow-md p-6 border-2 ${getLoadColor(load_balance?.status)}`}>
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">{getLoadIcon(load_balance?.status)}</span>
            <h2 className="text-xl font-bold">Load Balance: {load_balance?.status}</h2>
          </div>
          <p className="text-gray-600 italic">
            {load_balance?.message}
          </p>
        </div>

        {/* ── 4. STRENGTHS + GROWTH EDGES ── */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-green-700 mb-3">✓ Top Strengths</h3>
            <ul className="space-y-2">
              {strengths?.map((s, i) => (
                <li key={i} className="text-gray-700 font-medium">{s}</li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-orange-600 mb-3">⚡ Growth Edges</h3>
            <ul className="space-y-2">
              {growth_edges?.map((e, i) => (
                <li key={i} className="text-gray-700 font-medium">{e}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── 5. FOUR LENS TEASER SECTION ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">
            Your Profile Across 4 Lenses
          </h2>

          <div className="space-y-5">
            {lens_teasers && Object.entries(lens_teasers).map(([key, lens]) => (
              <div key={key} className="border border-gray-200 rounded-xl p-5">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-xl">{lensIcons[key] || '📋'}</span>
                  <h3 className="font-bold text-indigo-900">{lens.title}</h3>
                </div>
                <p className="text-gray-600 leading-relaxed mb-3">
                  {lens.teaser}
                </p>
                <button 
                  onClick={handleLensUpgrade}
                  disabled={upgradingFromLens}
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {upgradingFromLens ? '⏳ Processing...' : '🔒 Unlock Full Report →'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ── 6. LOCKED SECTIONS ── */}
        <LockedSections 
          features={locked_features} 
          assessmentId={assessmentId}
          userEmail={userEmail || metadata?.user_id}
        />

        {/* ── DOWNLOAD FREE SCORECARD PDF ── */}
        <div className="bg-white rounded-2xl shadow-md p-6 text-center">
          <h3 className="text-lg font-bold text-gray-800 mb-3">
            📄 Download Your Free ScoreCard
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Save your executive function profile as a PDF for your records.
          </p>
          
          {pdfError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <p className="font-semibold mb-1">Download Failed</p>
              <p>{pdfError}</p>
              <p className="text-xs mt-2 text-red-600">
                Check browser console (F12) for detailed error logs.
              </p>
            </div>
          )}
          
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf || !assessmentId}
            className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {downloadingPdf ? '⏳ Generating PDF...' : 'Download Free ScoreCard PDF'}
          </button>
          
          {!assessmentId && (
            <p className="text-xs text-red-600 mt-2">
              Assessment ID missing - cannot download PDF
            </p>
          )}
        </div>

        {/* ── FOOTER ── */}
        <div className="text-center pt-4 pb-8">
          <button
            onClick={onRestart}
            className="text-gray-500 hover:text-gray-700 text-sm underline transition-colors"
          >
            Take Assessment Again
          </button>
        </div>

      </div>
    </div>
  );
};

export default ScoreCard;
