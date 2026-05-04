import React from 'react';
import { TERMS_OF_USE, PRIVACY_POLICY, DATA_USE, LEGAL_VERSION } from './legalText';
import { FullLegalDisclaimer } from './Disclaimer';

// Render a structured legal document from a CONTENT object shaped like
// { title, intro, sections: [{ heading?, body?, bullets? }] }.
function renderDoc(doc) {
  return (
    <article className="prose prose-sm md:prose md:max-w-none text-gray-800">
      <h1 className="text-2xl sm:text-3xl font-bold text-indigo-900 break-words">{doc.title}</h1>
      <p className="text-xs text-gray-500 mt-1 mb-6">Effective {LEGAL_VERSION}</p>
      {doc.intro && <p className="text-sm sm:text-base">{doc.intro}</p>}
      {(doc.sections || []).map((sec, i) => (
        <section key={i} className="mt-6">
          {sec.heading && (
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">{sec.heading}</h2>
          )}
          {sec.body && <p className="text-sm sm:text-base">{sec.body}</p>}
          {sec.bullets && (
            <ul className="list-disc list-inside space-y-1 text-sm sm:text-base">
              {sec.bullets.map((b, j) => (
                <li key={j}>{b}</li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </article>
  );
}

const DOCS = {
  'terms-of-use': TERMS_OF_USE,
  'privacy-policy': PRIVACY_POLICY,
  'data-use': DATA_USE,
};

export default function LegalPage({ slug, onBack }) {
  const doc = DOCS[slug];
  if (!doc) {
    return (
      <div className="p-8 text-center text-gray-700">
        Legal document not found.{' '}
        <button
          onClick={onBack}
          className="text-indigo-600 hover:text-indigo-800 underline"
        >
          Go home
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6 sm:py-10 px-3 sm:px-4">
      <div className="max-w-3xl mx-auto bg-white shadow-sm rounded-2xl p-5 sm:p-8">
        <button
          onClick={onBack}
          className="mb-6 text-sm text-indigo-600 hover:text-indigo-800 font-semibold"
        >
          &larr; Back
        </button>
        {renderDoc(doc)}
        <div className="mt-8 sm:mt-10">
          <FullLegalDisclaimer />
        </div>
      </div>
    </div>
  );
}
