import React, { useEffect, useState } from 'react';
import axios from 'axios';

/**
 * PaymentSuccess
 * --------------
 * Landing page after Stripe checkout. We:
 *   1. Read the assessment_id and product from the success URL.
 *   2. Verify with the backend that the unlock has propagated.
 *   3. Stash the assessment_id in localStorage so App.js's normal flow
 *      can pick it up and route the user into the unified ScoreCard
 *      (which now has working "Cosmic Dashboard" and "AI Reports" buttons).
 *   4. Show a confirmation + "Continue" button that returns the user home.
 */
const PaymentSuccess = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [paidProducts, setPaidProducts] = useState([]);
  const [assessmentId, setAssessmentId] = useState(null);
  const [productJustPurchased, setProductJustPurchased] = useState(null);

  const PRODUCT_LABELS = {
    PERSONAL_LIFESTYLE: 'Personal / Lifestyle Lens',
    STUDENT_SUCCESS: 'Student Success Lens',
    PROFESSIONAL_LEADERSHIP: 'Professional / Leadership Lens',
    FAMILY_ECOSYSTEM: 'Family Ecosystem Lens',
    COSMIC_BUNDLE: 'Cosmic Integration Bundle',
    FINANCIAL_DEEP_DIVE: 'Financial Deep-Dive',
    HEALTH_DEEP_DIVE: 'Health & Fitness Deep-Dive',
    COMPATIBILITY: 'Compatibility Report',
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const aid = params.get('assessment_id');
    const product = params.get('product');
    setAssessmentId(aid);
    setProductJustPurchased(product);

    if (!aid) {
      setError('No assessment ID provided');
      setLoading(false);
      return;
    }

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 6;

    const poll = async () => {
      attempts += 1;
      try {
        const resp = await axios.get(`/api/v1/results/${aid}`);
        if (cancelled) return;
        if (resp.data?.success) {
          const products = resp.data.paid_products || [];
          setPaidProducts(products);

          // Persist a "deep-link" hint so App.js can resume the user into
          // the right place after they click Continue.
          try {
            localStorage.setItem('best_galaxy_pending_unlock', JSON.stringify({
              assessment_id: aid,
              paid_products: products,
              product,
              timestamp: new Date().toISOString(),
            }));
          } catch (e) {
            /* localStorage full or disabled */
          }

          const expected = product && !products.includes(product);
          if (expected && attempts < maxAttempts) {
            // Webhook may not have landed yet — retry briefly.
            setTimeout(poll, 1500);
            return;
          }
          setLoading(false);
        }
      } catch (err) {
        if (cancelled) return;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1500);
          return;
        }
        setError(err.response?.data?.detail || 'Failed to verify unlock');
        setLoading(false);
      }
    };

    poll();
    return () => { cancelled = true; };
  }, []);

  const handleContinue = () => {
    // Drop the ?assessment_id query string and go home. App.js will see the
    // pending unlock hint in localStorage and route the user to the
    // unified ScoreCard for that assessment.
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md mx-4 text-center">
          <div className="animate-spin rounded-full h-14 w-14 border-4 border-indigo-200 border-t-indigo-600 mx-auto mb-5"></div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">Confirming Your Unlock</h3>
          <p className="text-gray-500 text-sm">Verifying payment with our server…</p>
          <p className="text-xs text-gray-400 mt-3">This usually takes a few seconds</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Something went wrong</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-xs text-gray-500 mb-6">
            If you completed payment, your unlock may still be processing.
            You can refresh this page in a moment, or return home and check
            "My Reports".
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold rounded-lg transition-all shadow-md text-sm"
            >
              Retry
            </button>
            <button
              onClick={() => window.location.href = '/'}
              className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-all text-sm"
            >
              Return Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  const purchasedLabel = productJustPurchased
    ? PRODUCT_LABELS[productJustPurchased] || productJustPurchased
    : 'your unlock';

  const showCosmicCTA = paidProducts.includes('COSMIC_BUNDLE');
  const lensProducts = paidProducts.filter(p =>
    ['PERSONAL_LIFESTYLE', 'STUDENT_SUCCESS', 'PROFESSIONAL_LEADERSHIP', 'FAMILY_ECOSYSTEM'].includes(p),
  );
  const showLensCTA = lensProducts.length > 0 || showCosmicCTA;

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <div className="max-w-lg w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="text-5xl mb-3">✅</div>
        <h1 className="text-2xl font-bold text-indigo-900 mb-2">Payment Confirmed</h1>
        <p className="text-gray-600 mb-6">
          {purchasedLabel} is now unlocked for this assessment.
        </p>

        <div className="bg-indigo-50 rounded-xl p-4 mb-6 text-left">
          <p className="text-xs uppercase font-bold text-indigo-700 tracking-wide mb-2">
            Currently unlocked
          </p>
          {paidProducts.length === 0 ? (
            <p className="text-sm text-gray-500">
              Still processing — refresh this page in a moment.
            </p>
          ) : (
            <ul className="space-y-1">
              {paidProducts.map(p => (
                <li key={p} className="text-sm text-gray-700 flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  {PRODUCT_LABELS[p] || p}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-gray-50 rounded-xl p-4 mb-6 text-left text-sm text-gray-600">
          <p className="font-semibold text-gray-800 mb-2">Where to find your unlocked content:</p>
          <ul className="space-y-1">
            {showLensCTA && (
              <li>• <strong>📄 AI Reports</strong> — generate per-lens narratives (15 sections each)</li>
            )}
            {showCosmicCTA && (
              <li>• <strong>🌌 Cosmic Dashboard</strong> — Galaxy Map, Load Matrix &amp; integration synthesis</li>
            )}
            <li>• <strong>📊 My Reports</strong> — manage all your assessments</li>
          </ul>
          <p className="text-xs text-gray-500 mt-3">
            Both are accessible from the buttons at the bottom of your ScoreCard.
          </p>
        </div>

        <button
          onClick={handleContinue}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg"
        >
          Continue to Your Unlocked Report →
        </button>

        <p className="text-xs text-gray-400 mt-4">
          Assessment ID: {assessmentId?.slice(0, 8)}…
        </p>
      </div>
    </div>
  );
};

export default PaymentSuccess;
