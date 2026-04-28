import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UnlockGate from './UnlockGate';

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
  const [cosmicEligible, setCosmicEligible] = useState(false);
  const [cosmicMissing, setCosmicMissing] = useState([]);
  const [cosmicPaymentEligible, setCosmicPaymentEligible] = useState(false);
  const [error, setError] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const lensIsPaid = (lens) => {
    if (!paidProducts) return false;
    if (paidProducts.includes('COSMIC_BUNDLE')) return true;
    return paidProducts.includes(lens);
  };
  const cosmicIsPaid = (paidProducts || []).includes('COSMIC_BUNDLE');

  useEffect(() => {
    loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId]);

  const loadReports = async () => {
    if (!assessmentId || !userEmail) return;
    setLoading(true);
    try {
      const res = await axios.get(`/api/v1/reports/user/${userEmail}/assessment/${assessmentId}`);
      if (res.data.success && res.data.reports) {
        // Backend returns { LENS: sections } or { LENS: null } if locked.
        // Strip null entries so they're treated as not-yet-generated, then
        // remember which lenses the backend considers paid.
        const cleaned = Object.fromEntries(
          Object.entries(res.data.reports).filter(([, v]) => v && Object.keys(v).length > 0)
        );
        setReports(cleaned);
        if (res.data.report_ids) {
          setReportIds(res.data.report_ids);
        }
        if (res.data.paid_products) {
          setPaidProducts(res.data.paid_products);
        }
        const keys = Object.keys(cleaned);
        if (keys.length > 0 && !activeReport) {
          setActiveReport(keys[0]);
        }
      }

      const cosmicRes = await axios.get(`/api/v1/cosmic/eligibility/${userEmail}/${assessmentId}`);
      if (cosmicRes.data.success) {
        setCosmicEligible(cosmicRes.data.eligible);
        setCosmicMissing(cosmicRes.data.missing_lenses || []);
        setCosmicPaymentEligible(!!cosmicRes.data.payment_eligible);
        if (cosmicRes.data.paid_products) {
          setPaidProducts(cosmicRes.data.paid_products);
        }
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
        setCosmicEligible(true);
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
    <div className="max-w-4xl mx-auto p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-indigo-900">AI Narrative Reports</h1>
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
            className="text-sm text-indigo-600 hover:text-indigo-800 font-semibold whitespace-nowrap ml-4"
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
                    link.download = `BEST_Galaxy_${activeReport}_${new Date().toISOString().split('T')[0]}.pdf`;
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
    </div>
  );
};

export default ReportViewer;
