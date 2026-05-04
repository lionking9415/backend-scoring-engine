import React, { useState } from 'react';
import axios from 'axios';
import {
  CONSENT_CHECKBOXES,
  PRODUCT_NAME,
  LEGAL_VERSION,
} from './legalText';
import { ShortDisclaimer } from './Disclaimer';

// "Before You Begin" gate — must be passed before any assessment starts.
// 2 required checkboxes + 1 optional research consent.  On submit, posts
// to `/api/v1/consent` so we have a server-side audit trail with timestamp,
// user identifier, and which exact legal version they agreed to.
export default function ConsentGate({ user, onAgree, onCancel, onNavigate }) {
  const [checks, setChecks] = useState({
    terms: false,
    responsibility: false,
    research: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const allRequiredChecked = CONSENT_CHECKBOXES
    .filter((c) => c.required)
    .every((c) => checks[c.id]);

  const handleSubmit = async () => {
    if (!allRequiredChecked || submitting) return;
    setSubmitting(true);
    setError(null);

    const payload = {
      user_id: user?.email || user?.id || null,
      legal_version: LEGAL_VERSION,
      consents: { ...checks },
      user_agent:
        typeof navigator !== 'undefined' ? navigator.userAgent : null,
    };

    try {
      await axios.post('/api/v1/consent', payload);
    } catch (err) {
      // Don't block the user on a logging failure — local consent is what
      // counts for UX. Log a warning so we can investigate later.
      console.warn('Consent log failed (continuing anyway):', err);
    }

    try {
      const stored = {
        ...payload,
        recorded_at: new Date().toISOString(),
      };
      localStorage.setItem('best_galaxy_consent', JSON.stringify(stored));
    } catch (e) {
      /* private mode */
    }

    setSubmitting(false);
    onAgree(checks);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-3 py-6 sm:p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-5 sm:p-8">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-indigo-900 mb-2">
          Before You Begin
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          Please review and acknowledge the items below to start the {PRODUCT_NAME} assessment.
        </p>

        <ShortDisclaimer className="mb-6" />

        <p className="text-sm text-gray-600 mb-4">
          Read the full{' '}
          <a
            href="/terms-of-use"
            onClick={(e) => {
              e.preventDefault();
              onNavigate?.('/terms-of-use');
            }}
            className="text-indigo-600 hover:text-indigo-800 underline"
          >
            Terms of Use
          </a>
          ,{' '}
          <a
            href="/privacy-policy"
            onClick={(e) => {
              e.preventDefault();
              onNavigate?.('/privacy-policy');
            }}
            className="text-indigo-600 hover:text-indigo-800 underline"
          >
            Privacy Policy
          </a>
          , and{' '}
          <a
            href="/data-use"
            onClick={(e) => {
              e.preventDefault();
              onNavigate?.('/data-use');
            }}
            className="text-indigo-600 hover:text-indigo-800 underline"
          >
            Data Use Disclosure
          </a>
          .
        </p>

        <div className="space-y-4 mb-8">
          {CONSENT_CHECKBOXES.map((c) => (
            <label
              key={c.id}
              className="flex gap-3 items-start cursor-pointer p-3 border border-gray-200 rounded-lg hover:bg-indigo-50 transition-colors"
            >
              <input
                type="checkbox"
                checked={checks[c.id]}
                onChange={(e) =>
                  setChecks((prev) => ({ ...prev, [c.id]: e.target.checked }))
                }
                className="mt-1 h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                aria-required={c.required}
              />
              <span className="text-sm text-gray-800 leading-snug">
                {c.label}
                {c.required ? (
                  <span className="ml-1 text-red-600 font-semibold">*</span>
                ) : (
                  <span className="ml-1 text-gray-400">(optional)</span>
                )}
              </span>
            </label>
          ))}
        </div>

        {error && (
          <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row-reverse gap-3">
          <button
            onClick={handleSubmit}
            disabled={!allRequiredChecked || submitting}
            className={`flex-1 sm:flex-none px-6 py-3 rounded-xl font-bold text-white transition-all ${
              allRequiredChecked && !submitting
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg'
                : 'bg-gray-300 cursor-not-allowed'
            }`}
          >
            {submitting ? 'Saving\u2026' : 'I Agree & Begin Galaxy Scan'}
          </button>
          {onCancel && (
            <button
              onClick={onCancel}
              className="flex-1 sm:flex-none px-6 py-3 rounded-xl font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        <p className="text-xs text-gray-400 mt-6">
          Required fields are marked with <span className="text-red-600">*</span>. Legal version: v{LEGAL_VERSION}.
        </p>
      </div>
    </div>
  );
}
