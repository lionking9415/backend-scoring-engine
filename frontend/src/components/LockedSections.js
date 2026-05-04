import React, { useState } from 'react';
import axios from 'axios';
import { PAYMENT_ACK } from '../legal/legalText';

const LockedSections = ({
  features,
  assessmentId,
  userEmail,
  product = 'COSMIC_BUNDLE',
  ctaLabel = 'Unlock Full Galaxy',
  helperCopy = "You've seen the surface. Now see the system.",
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!features || features.length === 0) return null;

  const handleUpgrade = async () => {
    if (!assessmentId) {
      setError('No assessment ID available');
      return;
    }

    if (!userEmail) {
      setError('Please log in to unlock the full report');
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
          success_url: `${window.location.origin}/success?assessment_id=${assessmentId}`,
          cancel_url: window.location.href,
        }
      });

      if (response.data.success && response.data.session) {
        if (response.data.session.checkout_url) {
          window.location.href = response.data.session.checkout_url;
        } else if (response.data.session.error) {
          setError(response.data.session.error);
          setLoading(false);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create checkout session');
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-5">
        Deeper Layers Await
      </h2>

      <div className="space-y-3">
        {features.map((feat, idx) => (
          <div
            key={idx}
            className="relative overflow-hidden rounded-xl border border-gray-200 p-4"
          >
            {/* Blur overlay */}
            <div className="absolute inset-0 backdrop-blur-[2px] bg-white/60 z-10 flex items-center justify-center">
              <div className="text-center px-4">
                <span className="text-2xl block mb-1">🔒</span>
                <p className="text-gray-700 text-sm font-medium">{feat.message}</p>
              </div>
            </div>

            {/* Faux content behind blur */}
            <div className="opacity-30 select-none" aria-hidden="true">
              <h3 className="font-bold text-gray-800 mb-2">{feat.name}</h3>
              <div className="space-y-1">
                <div className="h-3 bg-gray-300 rounded w-full"></div>
                <div className="h-3 bg-gray-300 rounded w-5/6"></div>
                <div className="h-3 bg-gray-300 rounded w-4/6"></div>
                <div className="h-3 bg-gray-200 rounded w-3/6"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Upgrade CTA */}
      <div className="mt-6 text-center">
        <p className="text-gray-600 text-sm mb-2 italic">
          {helperCopy}
        </p>
        <p className="text-gray-500 text-xs mb-4">
          Your full report includes your personalized AIMS for the BEST™ intervention pathway.
        </p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
        
        <button 
          onClick={handleUpgrade}
          disabled={loading}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-xl text-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : ctaLabel}
        </button>
        <p className="text-gray-400 text-xs mt-2">
          {loading ? 'Redirecting to secure checkout...' : 'Secure payment via Stripe'}
        </p>
        <p className="text-gray-500 text-xs italic mt-2">
          {PAYMENT_ACK}
        </p>
      </div>
    </div>
  );
};

export default LockedSections;
