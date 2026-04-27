import React, { useState } from 'react';
import axios from 'axios';

/**
 * UnlockGate
 * ----------
 * Renders a blurred preview + Stripe-checkout CTA for a paywalled product.
 * Used by ReportViewer (per-lens) and CosmicDashboard (cosmic bundle).
 *
 * Props:
 *   product       — SKU id (e.g. "STUDENT_SUCCESS", "COSMIC_BUNDLE")
 *   title         — headline shown to the user
 *   description   — small-text explainer
 *   assessmentId  — required for checkout metadata
 *   userEmail     — required for Stripe customer email
 *   ctaLabel      — button text
 *   children      — the previewable content (rendered behind a blur)
 */
const UnlockGate = ({
  product,
  title,
  description,
  assessmentId,
  userEmail,
  ctaLabel,
  children,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUnlock = async () => {
    if (!assessmentId) {
      setError('No assessment ID available');
      return;
    }
    if (!userEmail) {
      setError('Please log in to unlock this content');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/v1/payment/create-checkout', null, {
        params: {
          assessment_id: assessmentId,
          customer_email: userEmail,
          product,
          success_url: `${window.location.origin}/success?assessment_id=${assessmentId}&product=${product}`,
          cancel_url: window.location.href,
        },
      });
      if (response.data?.success && response.data.session?.checkout_url) {
        window.location.href = response.data.session.checkout_url;
      } else {
        setError(response.data?.session?.error || 'Failed to start checkout');
        setLoading(false);
      }
    } catch (err) {
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to start checkout');
      setLoading(false);
    }
  };

  return (
    <div className="relative rounded-2xl border border-gray-200 bg-white overflow-hidden">
      {/* Faux preview behind blur */}
      <div
        className="opacity-40 pointer-events-none select-none p-6"
        aria-hidden="true"
      >
        {children || (
          <div className="space-y-2">
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-full"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
          </div>
        )}
      </div>

      {/* Lock overlay + CTA */}
      <div className="absolute inset-0 backdrop-blur-[3px] bg-white/70 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="text-3xl mb-2">🔒</div>
          <h3 className="text-lg font-bold text-gray-800 mb-1">{title}</h3>
          {description && (
            <p className="text-sm text-gray-600 mb-4">{description}</p>
          )}
          {error && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              {error}
            </div>
          )}
          <button
            onClick={handleUnlock}
            disabled={loading}
            className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold rounded-xl shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Redirecting…' : ctaLabel || `Unlock for ${product}`}
          </button>
          <p className="text-[10px] text-gray-400 mt-2">Secure payment via Stripe</p>
        </div>
      </div>
    </div>
  );
};

export default UnlockGate;
