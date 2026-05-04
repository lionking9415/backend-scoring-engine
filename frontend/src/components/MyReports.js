import React, { useEffect, useMemo, useState, useCallback } from 'react';
import axios from 'axios';
import { SkeletonCard, ErrorAlert } from './LoadingSpinner';

// Page size for the My Reports list. Anything below this threshold renders
// the full list with no pagination affordance, so the typical 1-3-report
// case is unaffected by the chrome.
const PAGE_SIZE = 10;

const MyReports = ({ userEmail, onViewReport, onBack }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1); // 1-indexed for human-friendly UI

  const fetchReports = useCallback(async () => {
    if (!userEmail) {
      setError('No user email provided');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/v1/user/${encodeURIComponent(userEmail)}/reports`);
      if (response.data.success) {
        setReports(response.data.reports);
      } else {
        setError('Failed to load reports');
      }
    } catch (err) {
      console.error('Error fetching reports:', err);
      const detail = err.response?.data?.detail;
      if (!err.response) {
        setError('Unable to connect to the server. Please check your internet connection.');
      } else {
        setError(typeof detail === 'string' ? detail : 'Failed to load reports. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [userEmail]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Derive the current page's slice + total page count.  Memoized so the
  // map() over reports doesn't re-run on every unrelated re-render.
  const { totalPages, pagedReports, startIdx, endIdx } = useMemo(() => {
    const total = Math.max(1, Math.ceil(reports.length / PAGE_SIZE));
    const safePage = Math.min(page, total); // guard against stale state
    const start = (safePage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, reports.length);
    return {
      totalPages: total,
      pagedReports: reports.slice(start, end),
      startIdx: start,
      endIdx: end,
    };
  }, [reports, page]);

  // Keep `page` in range whenever reports collection shrinks (e.g. refresh
  // after a delete). We always want to land on a populated page.
  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  // Maps every SKU to a short label + tile colour. Used to render
  // per-product badges that reflect what this assessment has actually
  // unlocked (driven by `paid_products`, not the legacy `report_type`
  // column which is a required placeholder on every assessment row).
  const PRODUCT_BADGES = {
    PERSONAL_LIFESTYLE:      { label: 'Personal / Lifestyle',      color: 'bg-purple-100 text-purple-800 border-purple-200' },
    STUDENT_SUCCESS:         { label: 'Student Success',           color: 'bg-blue-100 text-blue-800 border-blue-200' },
    PROFESSIONAL_LEADERSHIP: { label: 'Professional / Leadership', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
    FAMILY_ECOSYSTEM:        { label: 'Family / Ecosystem',        color: 'bg-pink-100 text-pink-800 border-pink-200' },
    COSMIC_BUNDLE:           { label: 'Cosmic Bundle',             color: 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white border-transparent' },
    FINANCIAL_DEEP_DIVE:     { label: 'Financial Deep-Dive',       color: 'bg-amber-100 text-amber-800 border-amber-200' },
    HEALTH_DEEP_DIVE:        { label: 'Health Deep-Dive',          color: 'bg-teal-100 text-teal-800 border-teal-200' },
    COMPATIBILITY:           { label: 'Compatibility',             color: 'bg-rose-100 text-rose-800 border-rose-200' },
  };

  // Renders the access-tier summary for one assessment row. Reads from
  // the authoritative `paid_products` list (not the legacy
  // `payment_status` flag, which can lag the per-SKU data on legacy
  // rows). Free assessments get a single "Free ScoreCard" badge; paid
  // assessments get one badge per unlocked SKU, with the Cosmic Bundle
  // collapsing the four lens badges so we don't double-count.
  const renderAccessBadges = (report) => {
    const paidProducts = Array.isArray(report.paid_products)
      ? report.paid_products
      : [];

    if (paidProducts.length === 0) {
      return (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
          Free ScoreCard
        </span>
      );
    }

    // If Cosmic Bundle is unlocked, show only that — it implicitly
    // covers all four lenses, so listing them separately is noise.
    const display = paidProducts.includes('COSMIC_BUNDLE')
      ? ['COSMIC_BUNDLE', ...paidProducts.filter(p => p !== 'COSMIC_BUNDLE' && !['PERSONAL_LIFESTYLE','STUDENT_SUCCESS','PROFESSIONAL_LEADERSHIP','FAMILY_ECOSYSTEM'].includes(p))]
      : paidProducts;

    return (
      <>
        {display.map((sku) => {
          const meta = PRODUCT_BADGES[sku] || { label: sku, color: 'bg-gray-100 text-gray-800 border-gray-200' };
          return (
            <span
              key={sku}
              className={`px-2 py-1 rounded-full text-xs font-semibold border ${meta.color}`}
            >
              {sku === 'COSMIC_BUNDLE' ? '⭐ ' : ''}{meta.label}
            </span>
          );
        })}
      </>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 px-3 py-4 sm:p-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8 mb-6">
            <div className="mb-6">
              <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse" />
            </div>
            <div className="space-y-4">
              <SkeletonCard lines={3} />
              <SkeletonCard lines={2} />
              <SkeletonCard lines={3} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 px-3 py-4 sm:p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-6">
            <div className="min-w-0">
              <h1 className="text-2xl sm:text-3xl font-bold text-indigo-900">My Reports</h1>
              <p className="text-sm text-gray-600 mt-1">View all your assessment reports</p>
            </div>
            <button
              onClick={onBack}
              className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm sm:text-base transition-colors self-start sm:self-auto whitespace-nowrap"
            >
              &larr; Back to Home
            </button>
          </div>

          {error && (
            <ErrorAlert
              error={error}
              onRetry={fetchReports}
              onDismiss={() => setError(null)}
              className="mb-6"
            />
          )}

          {reports.length === 0 && !error && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">No Reports Yet</h2>
              <p className="text-gray-600 mb-6">
                You haven't completed any assessments yet. Take your first assessment to get started!
              </p>
              <button
                onClick={onBack}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-xl transition-all duration-200"
              >
                Take Assessment
              </button>
            </div>
          )}

          {reports.length > 0 && (
            <div className="space-y-4">
              {pagedReports.map((report) => (
                <div
                  key={report.id}
                  className="border border-gray-200 rounded-xl p-4 sm:p-5 hover:shadow-md transition-shadow cursor-pointer bg-white"
                  onClick={() => onViewReport(report.id, report.payment_status)}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        {renderAccessBadges(report)}
                      </div>

                      <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-1 break-words">
                        {report.archetype_id ? report.archetype_id.replace(/_/g, ' ') : 'Assessment Report'}
                      </h3>

                      <p className="text-xs sm:text-sm text-gray-500">
                        {formatDate(report.created_at)}
                      </p>

                      {report.quadrant && (
                        <p className="text-xs sm:text-sm text-gray-600 mt-2">
                          <span className="font-medium">Quadrant:</span> {report.quadrant.replace(/_/g, ' ')}
                        </p>
                      )}
                    </div>

                    <div className="sm:text-right shrink-0">
                      <button
                        className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewReport(report.id, report.payment_status);
                        }}
                      >
                        View Report &rarr;
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination — hidden when the list fits on a single page. */}
          {reports.length > PAGE_SIZE && (
            <Pagination
              page={page}
              totalPages={totalPages}
              onChange={(p) => {
                setPage(p);
                // Scroll the user back to the top of the list so the page
                // change feels like a "page change" and not a silent state
                // mutation buried below the fold.
                if (typeof window !== 'undefined') {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }
              }}
            />
          )}
        </div>

        <div className="text-center text-sm text-gray-600">
          {reports.length > PAGE_SIZE ? (
            <p>
              Showing {startIdx + 1}&ndash;{endIdx} of {reports.length} reports
            </p>
          ) : (
            <p>
              Showing {reports.length} report{reports.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Compact numeric pagination with prev/next + ellipses for long ranges.
// Kept as a local helper so the page logic and styling stay close to the
// only place that uses it. If we ever need it elsewhere, lift it out.
function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null;

  // Decide which page-number buttons to render. We always show the first,
  // the last, the current, and one neighbour on each side; everything else
  // becomes an ellipsis. Keeps the row to a fixed footprint regardless of
  // whether the user has 11 reports or 1100.
  const pages = [];
  const push = (n) => {
    if (!pages.includes(n)) pages.push(n);
  };
  push(1);
  for (let p = page - 1; p <= page + 1; p += 1) {
    if (p > 1 && p < totalPages) push(p);
  }
  if (totalPages > 1) push(totalPages);
  pages.sort((a, b) => a - b);

  // Insert null where there's a gap so we can render an ellipsis.
  const withGaps = [];
  for (let i = 0; i < pages.length; i += 1) {
    if (i > 0 && pages[i] - pages[i - 1] > 1) withGaps.push(null);
    withGaps.push(pages[i]);
  }

  const baseBtn =
    'min-w-[2.25rem] h-9 px-3 rounded-lg text-sm font-medium transition-colors';
  const idleBtn = `${baseBtn} text-gray-700 hover:bg-gray-100 border border-gray-200 bg-white`;
  const activeBtn = `${baseBtn} text-white bg-indigo-600 border border-indigo-600`;
  const disabledBtn = `${baseBtn} text-gray-300 bg-white border border-gray-200 cursor-not-allowed`;

  return (
    <nav
      className="mt-6 flex items-center justify-center gap-2 flex-wrap"
      aria-label="Pagination"
    >
      <button
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        className={page <= 1 ? disabledBtn : idleBtn}
        aria-label="Previous page"
      >
        &larr; Prev
      </button>

      {withGaps.map((p, i) =>
        p === null ? (
          <span key={`gap-${i}`} className="px-1 text-gray-400 select-none">
            &hellip;
          </span>
        ) : (
          <button
            type="button"
            key={p}
            onClick={() => onChange(p)}
            aria-current={p === page ? 'page' : undefined}
            className={p === page ? activeBtn : idleBtn}
          >
            {p}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
        className={page >= totalPages ? disabledBtn : idleBtn}
        aria-label="Next page"
      >
        Next &rarr;
      </button>
    </nav>
  );
}

export default MyReports;
