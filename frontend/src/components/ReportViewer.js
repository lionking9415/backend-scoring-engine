import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import UnlockGate from './UnlockGate';
import { ShortDisclaimer, FullLegalDisclaimer } from '../legal/Disclaimer';

// The four lens reports that must exist before Cosmic Integration synthesis
// is allowed. Mirrors `check_cosmic_eligibility` in scoring_engine/report_generator.py.
const REQUIRED_COSMIC_LENSES = [
  'STUDENT_SUCCESS',
  'PERSONAL_LIFESTYLE',
  'PROFESSIONAL_LEADERSHIP',
  'FAMILY_ECOSYSTEM',
];

const SECTION_META = {
  galaxy_snapshot: { icon: '🌠', title: 'Galaxy Snapshot', color: '#6366F1' },
  galaxy_placement: { icon: '🪐', title: 'Galaxy Placement', color: '#8B5CF6' },
  archetype_profile: { icon: '🧬', title: 'Archetype Profile', color: '#A78BFA' },
  ef_ecosystem: { icon: '⚙️', title: 'Executive Function Ecosystem', color: '#7C3AED' },
  financial_ef_profile: { icon: '💰', title: 'Financial Executive Functioning Profile™', color: '#059669' },
  health_ef_profile: { icon: '🏃', title: 'Health & Fitness Executive Functioning Profile™', color: '#2563EB' },
  pei_analysis: { icon: '🌍', title: 'PEI Analysis (External Load)', color: '#DC2626' },
  bhp_analysis: { icon: '🧠', title: 'BHP Analysis (Internal Capacity)', color: '#16A34A' },
  pei_bhp_interaction: { icon: '🔗', title: 'PEI × BHP Interaction', color: '#D97706' },
  strength_profile: { icon: '🌱', title: 'Strength Profile', color: '#059669' },
  growth_edges: { icon: '⚠️', title: 'Growth Edges / Load Sensitivity Zones', color: '#EA580C' },
  aims_plan: { icon: '🚀', title: 'AIMS for the BEST™', color: '#7C3AED' },
  pattern_continuity: { icon: '🔁', title: 'Pattern Continuity Section™', color: '#6366F1' },
  expansion_pathway: { icon: '🔭', title: 'Expansion Pathway Section™', color: '#8B5CF6' },
  cosmic_summary: { icon: '🌌', title: 'Cosmic Summary', color: '#4F46E5' },
  // Cosmic-specific sections
  cosmic_snapshot: { icon: '🌠', title: 'Cosmic Snapshot', color: '#6366F1' },
  galaxy_convergence_map: { icon: '🌌', title: 'Galaxy Convergence Map™', color: '#8B5CF6' },
  load_balance_matrix: { icon: '⚖️', title: 'Load Balance Matrix™', color: '#7C3AED' },
  cross_domain_load_transfer: { icon: '🔗', title: 'Cross-Domain Load Transfer Analysis', color: '#D97706' },
  core_system_identity: { icon: '🧠', title: 'Core System Identity Under Load', color: '#DC2626' },
  global_strength_architecture: { icon: '🌱', title: 'Global Strength Architecture', color: '#059669' },
  system_wide_sensitivity: { icon: '⚠️', title: 'System-Wide Load Sensitivity Zones', color: '#EA580C' },
  pattern_continuity_amplified: { icon: '🔄', title: 'Pattern Continuity Amplified™', color: '#6366F1' },
  cosmic_aims: { icon: '🧭', title: 'AIMS for the BEST™ — Cosmic Level', color: '#7C3AED' },
  // Lens-exclusive sections (Addendum Phase 3)
  academic_performance_impact: { icon: '📚', title: 'Academic Performance Impact™', color: '#F59E0B' },
  lifestyle_stability_index: { icon: '🏠', title: 'Lifestyle Stability Index™', color: '#10B981' },
  execution_productivity_profile: { icon: '⚡', title: 'Execution & Productivity Profile™', color: '#3B82F6' },
  family_system_dynamics: { icon: '👪', title: 'Family System Dynamics™', color: '#EC4899' },
};

const LENS_LABELS = {
  STUDENT_SUCCESS: { label: 'Student Success', icon: '🎓', color: '#6366F1' },
  PERSONAL_LIFESTYLE: { label: 'Personal / Lifestyle', icon: '🧍', color: '#8B5CF6' },
  PROFESSIONAL_LEADERSHIP: { label: 'Professional / Leadership', icon: '💼', color: '#2563EB' },
  FAMILY_ECOSYSTEM: { label: 'Family EF Ecosystem', icon: '👨‍👩‍👧', color: '#059669' },
  FULL_GALAXY: { label: 'Cosmic Integration', icon: '🌌', color: '#7C3AED' },
};

const LENS_SECTION_ORDER = [
  'galaxy_snapshot', 'galaxy_placement', 'archetype_profile', 'ef_ecosystem',
  'financial_ef_profile', 'health_ef_profile', 'pei_analysis', 'bhp_analysis',
  'pei_bhp_interaction', 'strength_profile', 'growth_edges', 'aims_plan',
  'pattern_continuity', 'expansion_pathway', 'cosmic_summary',
];

const COSMIC_SECTION_ORDER = [
  'cosmic_snapshot', 'galaxy_convergence_map', 'load_balance_matrix',
  'cross_domain_load_transfer', 'core_system_identity', 'global_strength_architecture',
  'system_wide_sensitivity', 'pattern_continuity_amplified', 'cosmic_aims',
  'expansion_pathway', 'cosmic_summary',
];

const SectionCard = ({ sectionKey, content, index }) => {
  const [expanded, setExpanded] = useState(index < 3);
  const meta = SECTION_META[sectionKey] || { icon: '📄', title: sectionKey.replace(/_/g, ' '), color: '#6B7280' };

  if (!content || !content.trim()) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 rounded-xl bg-white shadow-sm border border-gray-100 hover:shadow-md transition-all text-left"
      >
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
          style={{ backgroundColor: meta.color + '18' }}
        >
          {meta.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-800 text-sm">{meta.title}</h3>
          {!expanded && (
            <p className="text-xs text-gray-400 truncate mt-0.5">
              {content.substring(0, 100)}...
            </p>
          )}
        </div>
        <span className="text-gray-400 text-sm flex-shrink-0">
          {expanded ? '▼' : '▶'}
        </span>
      </button>
      {expanded && (
        <div className="mt-1 mx-2 p-5 bg-white rounded-b-xl border border-t-0 border-gray-100">
          {content.split('\n\n').map((paragraph, i) => (
            <p key={i} className="text-gray-700 text-sm leading-relaxed mb-3 last:mb-0">
              {paragraph.split('\n').map((line, j) => (
                <React.Fragment key={j}>
                  {line}
                  {j < paragraph.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))}
            </p>
          ))}
        </div>
      )}
    </div>
  );
};

const ReportViewer = ({ assessmentId, userEmail, paidProducts: paidProductsProp = [], onBack }) => {
  const [reports, setReports] = useState({});
  const [reportIds, setReportIds] = useState({});
  const [paidProducts, setPaidProducts] = useState(paidProductsProp);
  const [activeReport, setActiveReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [cosmicPaymentEligible, setCosmicPaymentEligible] = useState(false);
  const [error, setError] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Derive cosmic eligibility client-side from the reports we currently
  // hold. This makes the "Generate Cosmic Integration" button enable
  // *immediately* after the 4th lens is generated — without waiting for
  // a manual refresh or an extra API roundtrip. The backend re-validates
  // on POST /api/v1/cosmic/generate so we're not skipping any guardrail.
  const { cosmicEligible, cosmicMissing } = useMemo(() => {
    const have = new Set(
      Object.keys(reports || {}).filter(
        (k) => reports[k] && Object.keys(reports[k]).length > 0,
      ),
    );
    const missing = REQUIRED_COSMIC_LENSES.filter((l) => !have.has(l));
    return {
      cosmicEligible: missing.length === 0,
      cosmicMissing: missing,
    };
  }, [reports]);

  const lensIsPaid = (lens) => {
    if (!paidProducts) return false;
    if (paidProducts.includes('COSMIC_BUNDLE')) return true;
    return paidProducts.includes(lens);
  };
  const cosmicIsPaid = (paidProducts || []).includes('COSMIC_BUNDLE');

  // Refreshes the cosmic eligibility data we *can't* derive on the client
  // (server-side payment eligibility, paid_products SKUs). Called on mount
  // and again after each lens generation so the UI stays in sync with the
  // backend's authoritative view.
  const refreshCosmicEligibility = useCallback(async () => {
    if (!assessmentId || !userEmail) return null;
    try {
      const res = await axios.get(
        `/api/v1/cosmic/eligibility/${userEmail}/${assessmentId}`,
      );
      if (res.data?.success) {
        setCosmicPaymentEligible(!!res.data.payment_eligible);
        if (Array.isArray(res.data.paid_products)) {
          setPaidProducts(res.data.paid_products);
        }
        return res.data;
      }
    } catch (err) {
      console.warn('Cosmic eligibility refresh failed:', err);
    }
    return null;
  }, [assessmentId, userEmail]);

  useEffect(() => {
    loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId]);

  const loadReports = async () => {
    if (!assessmentId || !userEmail) return;
    setLoading(true);
    try {
      // Step 1 — pull the four lens reports + their IDs.
      // Note: the backend `get_user_lens_reports` excludes FULL_GALAXY, so
      // `res.data.reports` will never contain the cosmic narrative even
      // if one is saved. Cosmic is loaded separately below (Step 3).
      const res = await axios.get(`/api/v1/reports/user/${userEmail}/assessment/${assessmentId}`);
      let nextReports = {};
      let nextReportIds = {};
      let mergedPaidProducts = paidProducts || [];

      if (res.data.success && res.data.reports) {
        nextReports = Object.fromEntries(
          Object.entries(res.data.reports).filter(([, v]) => v && Object.keys(v).length > 0)
        );
        if (res.data.report_ids) {
          nextReportIds = { ...res.data.report_ids };
        }
        if (res.data.paid_products) {
          mergedPaidProducts = res.data.paid_products;
        }
      }

      // Step 2 — cosmic eligibility (also refreshes paid_products).
      // Note: `cosmicEligible` / `cosmicMissing` are derived from `reports`
      // via useMemo — we don't need to set them from the API response.
      let cosmicPaid = mergedPaidProducts.includes('COSMIC_BUNDLE');
      try {
        const cosmicRes = await axios.get(`/api/v1/cosmic/eligibility/${userEmail}/${assessmentId}`);
        if (cosmicRes.data.success) {
          setCosmicPaymentEligible(!!cosmicRes.data.payment_eligible);
          if (cosmicRes.data.paid_products) {
            mergedPaidProducts = cosmicRes.data.paid_products;
            cosmicPaid = mergedPaidProducts.includes('COSMIC_BUNDLE');
          }
        }
      } catch (err) {
        console.warn('Cosmic eligibility check failed:', err);
      }

      // Step 3 — pull the saved cosmic narrative if the user has paid for it.
      // Without this, every browser refresh would force the user back through
      // a fresh generation (re-spending OpenAI tokens) even though the report
      // was already persisted on the server.
      if (cosmicPaid) {
        try {
          const cosmicReportRes = await axios.get(
            `/api/v1/cosmic/report/${userEmail}/${assessmentId}`,
          );
          const data = cosmicReportRes.data;
          if (data?.sections && Object.keys(data.sections).length > 0) {
            nextReports = { ...nextReports, FULL_GALAXY: data.sections };
            const cosmicId = data.id || data.report_id;
            if (cosmicId) {
              nextReportIds = { ...nextReportIds, FULL_GALAXY: cosmicId };
            }
          }
        } catch (err) {
          // 404 simply means no cosmic generated yet — not an error worth
          // surfacing. Anything else is logged for diagnostics.
          if (err.response?.status !== 404) {
            console.warn('Failed to load saved cosmic report:', err);
          }
        }
      }

      setReports(nextReports);
      setReportIds(nextReportIds);
      setPaidProducts(mergedPaidProducts);
      const keys = Object.keys(nextReports);
      if (keys.length > 0 && !activeReport) {
        // Prefer FULL_GALAXY when present so users land on the cosmic
        // narrative they paid for, otherwise the first available lens.
        setActiveReport(keys.includes('FULL_GALAXY') ? 'FULL_GALAXY' : keys[0]);
      }
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (reportType) => {
    setError(null);

    // Paywall: if this lens isn't unlocked, send the user to Stripe instead
    // of attempting a backend call that will return 402.
    if (!lensIsPaid(reportType)) {
      try {
        const res = await axios.post('/api/v1/payment/create-checkout', null, {
          params: {
            assessment_id: assessmentId,
            customer_email: userEmail,
            product: reportType,
            success_url: `${window.location.origin}/success?assessment_id=${assessmentId}&product=${reportType}`,
            cancel_url: window.location.href,
          },
        });
        if (res.data?.success && res.data.session?.checkout_url) {
          window.location.href = res.data.session.checkout_url;
          return;
        }
        setError(res.data?.session?.error || 'Failed to start checkout');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to start checkout');
      }
      return;
    }

    setGenerating(true);
    try {
      const res = await axios.post('/api/v1/reports/generate', {
        assessment_id: assessmentId,
        report_type: reportType,
        user_id: userEmail,
      });
      if (res.data.success) {
        setReports(prev => ({ ...prev, [reportType]: res.data.report.sections }));
        if (res.data.report.report_id) {
          setReportIds(prev => ({ ...prev, [reportType]: res.data.report.report_id }));
        }
        setActiveReport(reportType);
        // Re-sync server-side payment/eligibility state. The cosmic
        // *eligibility* flag itself is derived from `reports` via useMemo,
        // so the Cosmic Integration button enables the moment the 4th
        // lens is added — no refresh required.
        refreshCosmicEligibility();
      }
    } catch (err) {
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Report generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const generateCosmicReport = async () => {
    setError(null);

    if (!cosmicIsPaid) {
      try {
        const res = await axios.post('/api/v1/payment/create-checkout', null, {
          params: {
            assessment_id: assessmentId,
            customer_email: userEmail,
            product: 'COSMIC_BUNDLE',
            success_url: `${window.location.origin}/success?assessment_id=${assessmentId}&product=COSMIC_BUNDLE`,
            cancel_url: window.location.href,
          },
        });
        if (res.data?.success && res.data.session?.checkout_url) {
          window.location.href = res.data.session.checkout_url;
          return;
        }
        setError(res.data?.session?.error || 'Failed to start checkout');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to start checkout');
      }
      return;
    }

    setGenerating(true);
    try {
      const res = await axios.post('/api/v1/cosmic/generate', {
        assessment_id: assessmentId,
        user_id: userEmail,
      });
      if (res.data.success) {
        setReports(prev => ({ ...prev, FULL_GALAXY: res.data.report.sections }));
        if (res.data.report.report_id) {
          setReportIds(prev => ({ ...prev, FULL_GALAXY: res.data.report.report_id }));
        }
        setActiveReport('FULL_GALAXY');
        // No need to set `cosmicEligible` — it's derived from `reports`
        // via useMemo. Refresh server-side payment state to stay accurate.
        refreshCosmicEligibility();
      }
    } catch (err) {
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Cosmic report generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const activeSections = activeReport ? reports[activeReport] : null;
  const sectionOrder = activeReport === 'FULL_GALAXY' ? COSMIC_SECTION_ORDER : LENS_SECTION_ORDER;
  const lensInfo = LENS_LABELS[activeReport] || {};

  return (
    <div className="max-w-4xl mx-auto px-3 py-4 sm:p-4">
      {/* TOP-OF-REPORT SHORT DISCLAIMER — required by
          docs/Legal Terms & Conditions.md §4 */}
      <ShortDisclaimer className="mb-4" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-indigo-900">AI Narrative Reports</h1>
          <p className="text-sm text-gray-500 mt-1">
            15-section AI-written interpretations of your assessment — one per lens.
          </p>
          <p className="text-xs text-gray-400 mt-1 italic">
            Looking for charts, scores, and bars? Download the{' '}
            <span className="font-semibold text-indigo-600">Data Report PDF</span> from your ScoreCard instead.
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-sm text-indigo-600 hover:text-indigo-800 font-semibold whitespace-nowrap self-start sm:ml-4 sm:shrink-0"
          >
            ← Back to Dashboard
          </button>
        )}
      </div>

      {/* Lens Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {Object.entries(LENS_LABELS).map(([key, lens]) => {
          if (key === 'FULL_GALAXY' && !reports[key] && !cosmicEligible) return null;
          const hasReport = !!reports[key];
          const isActive = activeReport === key;
          const isLocked = key === 'FULL_GALAXY' ? !cosmicIsPaid : !lensIsPaid(key);
          return (
            <button
              key={key}
              onClick={() => hasReport
                ? setActiveReport(key)
                : key === 'FULL_GALAXY' ? generateCosmicReport() : generateReport(key)}
              disabled={generating}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all border-2 ${
                isActive
                  ? 'border-indigo-600 bg-indigo-600 text-white shadow-md'
                  : hasReport
                    ? 'border-indigo-200 bg-white text-indigo-700 hover:bg-indigo-50'
                    : isLocked
                      ? 'border-dashed border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'
                      : 'border-dashed border-gray-300 bg-white text-gray-500 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              <span>{lens.icon}</span>
              <span>{lens.label}</span>
              {!hasReport && key !== 'FULL_GALAXY' && (
                isLocked ? (
                  <span className="text-xs opacity-80">🔒 Unlock</span>
                ) : (
                  <span className="text-xs opacity-70">+ Generate</span>
                )
              )}
              {!hasReport && key === 'FULL_GALAXY' && isLocked && (
                <span className="text-xs opacity-80">🔒 Unlock</span>
              )}
              {hasReport && <span className="text-xs opacity-70">✓</span>}
            </button>
          );
        })}
      </div>

      {/* Cosmic Integration Banner */}
      {!reports.FULL_GALAXY && (
        <div className={`mb-6 rounded-xl p-4 border-2 ${
          cosmicEligible && cosmicPaymentEligible
            ? 'border-purple-300 bg-gradient-to-r from-purple-50 to-indigo-50'
            : 'border-gray-200 bg-gray-50'
        }`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">🌌</span>
            <div className="flex-1">
              <h3 className="font-bold text-gray-800 text-sm">
                Cosmic Integration Report™
              </h3>
              {!cosmicEligible ? (
                <p className="text-xs text-gray-500 mt-0.5">
                  Generate all 4 lens reports first. Missing:{' '}
                  {cosmicMissing.map(m => LENS_LABELS[m]?.label || m).join(', ') || '—'}
                </p>
              ) : !cosmicPaymentEligible ? (
                <p className="text-xs text-amber-700 mt-0.5">
                  All 4 lenses generated. Purchase the Cosmic Bundle to unlock the integration synthesis.
                </p>
              ) : (
                <p className="text-xs text-purple-700 mt-0.5">
                  All 4 lenses ready and Cosmic Bundle unlocked. Generate your unified cross-domain analysis.
                </p>
              )}
            </div>
            {cosmicEligible && (
              <button
                onClick={generateCosmicReport}
                disabled={generating}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-bold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50"
              >
                {generating
                  ? 'Generating...'
                  : cosmicPaymentEligible
                    ? 'Generate Cosmic Report'
                    : '🔒 Unlock Cosmic Bundle'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading */}
      {(loading || generating) && (
        <div className="flex flex-col items-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-indigo-600 mb-4"></div>
          <p className="text-gray-600 font-medium">
            {generating ? 'Generating your personalized report...' : 'Loading reports...'}
          </p>
          {generating && (
            <p className="text-xs text-gray-400 mt-2">This may take 15-30 seconds</p>
          )}
        </div>
      )}

      {/* Report Content */}
      {!loading && !generating && activeSections && (
        <div>
          {/* Report Header */}
          <div
            className="rounded-xl p-5 mb-6 text-white"
            style={{ background: `linear-gradient(135deg, ${lensInfo.color || '#6366F1'}, ${lensInfo.color || '#6366F1'}CC)` }}
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">{lensInfo.icon}</span>
              <div>
                <h2 className="text-xl font-bold">
                  {lensInfo.label} {activeReport === 'FULL_GALAXY' ? '— Cosmic Narrative' : '— AI Narrative'}
                </h2>
                <p className="text-sm opacity-80">
                  {activeReport === 'FULL_GALAXY'
                    ? '11-section AI synthesis across all 4 lenses'
                    : '15-section AI-written interpretation of your scoring data'}
                </p>
              </div>
            </div>
          </div>

          {/* Sections */}
          {sectionOrder.map((key, idx) => (
            <SectionCard
              key={key}
              sectionKey={key}
              content={activeSections[key]}
              index={idx}
            />
          ))}

          {/* Download PDF */}
          {reportIds[activeReport] && (
            <div className="mt-6 text-center">
              <button
                onClick={async () => {
                  setDownloadingPdf(true);
                  try {
                    const res = await axios.get(
                      `/api/v1/export/ai-report-pdf/${reportIds[activeReport]}`,
                      { responseType: 'blob', timeout: 30000 }
                    );
                    const blob = new Blob([res.data], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    // Distinct kind-prefix so this AI Narrative PDF doesn't
                    // overwrite the same-lens Data Report PDF in the
                    // user's Downloads folder.
                    const today = new Date().toISOString().split('T')[0];
                    link.download = activeReport === 'FULL_GALAXY'
                      ? `BEST_Cosmic_Narrative_${today}.pdf`
                      : `BEST_Galaxy_AINarrative_${activeReport}_${today}.pdf`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                  } catch (err) {
                    console.error('PDF download failed:', err);
                    alert('Failed to download PDF. Please try again.');
                  } finally {
                    setDownloadingPdf(false);
                  }
                }}
                disabled={downloadingPdf}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>{downloadingPdf ? '⏳' : '📥'}</span>
                {downloadingPdf
                  ? 'Generating PDF...'
                  : activeReport === 'FULL_GALAXY'
                    ? 'Download Cosmic Narrative PDF'
                    : 'Download AI Narrative PDF'}
              </button>
            </div>
          )}

          {/* Validation Badge */}
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3">
            <span className="text-green-600 text-xl">✓</span>
            <div>
              <p className="text-sm font-semibold text-green-800">Report Quality Verified</p>
              <p className="text-xs text-green-600">
                All {sectionOrder.length} sections present • Language compliance checked • AIMS structure verified
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Empty State (no reports generated yet) */}
      {!loading && !generating && !activeSections && Object.keys(reports).length === 0 && (
        (paidProducts || []).length === 0 ? (
          <UnlockGate
            product="PERSONAL_LIFESTYLE"
            title="AI Narrative Reports are a premium feature"
            description="Unlock any lens to generate your personalized 15-section AI-written interpretation of your assessment."
            assessmentId={assessmentId}
            userEmail={userEmail}
            ctaLabel="Unlock Personal / Lifestyle Lens →"
          >
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-full"></div>
              <div className="h-3 bg-gray-200 rounded w-5/6"></div>
              <div className="h-3 bg-gray-200 rounded w-4/6"></div>
              <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          </UnlockGate>
        ) : (
          <div className="text-center py-16">
            <span className="text-5xl mb-4 block">✍️</span>
            <h3 className="text-xl font-bold text-gray-800 mb-2">No AI Narratives Yet</h3>
            <p className="text-gray-500 text-sm mb-6">
              Select a lens above to generate your first 15-section AI-written interpretation.
            </p>
            <button
              onClick={() => generateReport((paidProducts || [])[0] || 'PERSONAL_LIFESTYLE')}
              disabled={generating}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all"
            >
              Generate {LENS_LABELS[(paidProducts || [])[0]]?.label || 'Personal / Lifestyle'} AI Narrative
            </button>
          </div>
        )
      )}

      {/* END-OF-REPORT FULL LEGAL DISCLAIMER — required by
          docs/Legal Terms & Conditions.md §4 */}
      <FullLegalDisclaimer className="mt-10" />
    </div>
  );
};

export default ReportViewer;
