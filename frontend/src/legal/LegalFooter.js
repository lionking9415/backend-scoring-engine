import React from 'react';
import { INLINE_DISCLAIMER, ENTITY_NAME, PRODUCT_NAME, LEGAL_VERSION } from './legalText';

// Persistent footer rendered on every page.
// Links navigate via history.pushState so they integrate with App.js's
// URL-backed routing (no full page reloads).
export default function LegalFooter({ onNavigate }) {
  const go = (e, path) => {
    e.preventDefault();
    if (onNavigate) onNavigate(path);
    else window.location.assign(path);
  };

  const linkCls =
    'text-indigo-600 hover:text-indigo-800 underline underline-offset-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 rounded';

  return (
    <footer
      className="mt-auto border-t border-gray-200 bg-white/80 backdrop-blur px-4 py-3 text-xs text-gray-600"
      role="contentinfo"
    >
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <p className="leading-snug">
          <span className="font-medium text-gray-700">{INLINE_DISCLAIMER}</span>
          <span className="mx-2 text-gray-300">|</span>
          <span>
            &copy; {new Date().getFullYear()} {ENTITY_NAME} &mdash; {PRODUCT_NAME}
          </span>
        </p>
        <nav className="flex flex-wrap gap-x-4 gap-y-1" aria-label="Legal">
          <a href="/terms-of-use" className={linkCls} onClick={(e) => go(e, '/terms-of-use')}>
            Terms of Use
          </a>
          <a href="/privacy-policy" className={linkCls} onClick={(e) => go(e, '/privacy-policy')}>
            Privacy Policy
          </a>
          <a href="/data-use" className={linkCls} onClick={(e) => go(e, '/data-use')}>
            Data Use
          </a>
          <span className="text-gray-400">v{LEGAL_VERSION}</span>
        </nav>
      </div>
    </footer>
  );
}
