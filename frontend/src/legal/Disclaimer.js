import React from 'react';
import {
  SHORT_DISCLAIMER,
  INLINE_DISCLAIMER,
  FULL_DISCLAIMER_TITLE,
  FULL_DISCLAIMER_BODY,
  FULL_DISCLAIMER_BULLETS,
  FULL_DISCLAIMER_CLOSING,
} from './legalText';

// Tiny one-liner for cramped UI areas (dashboard headers, etc.).
export function InlineDisclaimer({ className = '' }) {
  return (
    <p className={`text-xs italic text-gray-500 ${className}`}>
      {INLINE_DISCLAIMER}
    </p>
  );
}

// 2–3 line pill — good for top of report panels and modal lead-ins.
export function ShortDisclaimer({ className = '' }) {
  return (
    <div
      className={`bg-amber-50 border-l-4 border-amber-400 text-amber-900 text-sm rounded-r-lg p-3 ${className}`}
      role="note"
      aria-label="Important Notice"
    >
      <p className="font-semibold mb-1">Important Notice</p>
      <p className="leading-snug">{SHORT_DISCLAIMER}</p>
    </div>
  );
}

// Full block — used at the end of every report and on the legal pages.
export function FullLegalDisclaimer({ className = '' }) {
  return (
    <section
      className={`bg-gray-50 border border-gray-200 rounded-xl p-6 text-sm text-gray-700 leading-relaxed ${className}`}
      aria-label={FULL_DISCLAIMER_TITLE}
    >
      <h3 className="text-base font-bold text-gray-900 mb-3">
        {FULL_DISCLAIMER_TITLE}
      </h3>
      {FULL_DISCLAIMER_BODY.map((para, i) => (
        <p key={i} className="mb-3">
          {para}
        </p>
      ))}
      <ul className="list-disc list-inside space-y-1 mb-3">
        {FULL_DISCLAIMER_BULLETS.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
      <p>{FULL_DISCLAIMER_CLOSING}</p>
    </section>
  );
}
