import React, { useState, useEffect, useCallback } from 'react';
import GalaxyMap from './GalaxyMap';
import LoadMatrix from './LoadMatrix';
import LoadFlow from './LoadFlow';
import StabilizersPanel from './StabilizersPanel';
import AimsTrack from './AimsTrack';

const COSMIC_SECTION_ORDER = [
  { key: 'cosmic_snapshot', title: 'Cosmic Snapshot', icon: '🌌' },
  { key: 'galaxy_convergence_map', title: 'Galaxy Convergence Map', icon: '🪐' },
  { key: 'archetype_evolution', title: 'Archetype Evolution', icon: '✨' },
  { key: 'cross_domain_load_transfer', title: 'Cross-Domain Load Transfer', icon: '🔁' },
  { key: 'compensation_patterns', title: 'Compensation Patterns', icon: '🛡️' },
  { key: 'system_wide_sensitivity', title: 'System-Wide Sensitivity', icon: '⚠️' },
  { key: 'stabilizers_across_universe', title: 'Stabilizers Across Your Universe', icon: '🌱' },
  { key: 'lens_overlay_summary', title: 'Lens Overlay Summary', icon: '🔍' },
  { key: 'cosmic_aims', title: 'Cosmic AIMS Pathway', icon: '🚀' },
  { key: 'long_term_trajectory', title: 'Long-Term Trajectory', icon: '🛰️' },
  { key: 'closing_synthesis', title: 'Closing Synthesis', icon: '⭐' },
];

const formatParagraph = (text) => {
  if (!text) return null;
  return String(text)
    .split(/\n{2,}/)
    .map((para, i) => (
      <p key={i} className="text-sm text-gray-700 leading-relaxed mb-3 whitespace-pre-line">
        {para.trim()}
      </p>
    ));
};

const CosmicDashboard = ({
  data,
  onViewReports,
  apiBase,
  userId,
  assessmentId,
}) => {
  const [cosmicReport, setCosmicReport] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportError, setReportError] = useState(null);
  const [generating, setGenerating] = useState(false);

  const baseUrl = apiBase || '';
  const meta = data?.metadata || {};
  const resolvedUserId = userId || meta.user_id;
  const resolvedAssessmentId = assessmentId || meta.assessment_id;

  // Eligibility + already-generated cosmic report
  useEffect(() => {
    let cancelled = false;
    const fetchAll = async () => {
      if (!resolvedUserId || !resolvedAssessmentId) return;
      setLoadingReport(true);
      setReportError(null);
      try {
        const eligRes = await fetch(
          `${baseUrl}/api/v1/cosmic/eligibility/${resolvedUserId}/${resolvedAssessmentId}`
        );
        if (eligRes.ok) {
          const elig = await eligRes.json();
          if (!cancelled) setEligibility(elig);
        }

        // Try to fetch a previously generated cosmic report
        const repRes = await fetch(
          `${baseUrl}/api/v1/cosmic/report/${resolvedUserId}/${resolvedAssessmentId}`
        );
        if (repRes.ok) {
          const rep = await repRes.json();
          if (!cancelled && rep && rep.sections) {
            setCosmicReport(rep);
          }
        }
      } catch (err) {
        if (!cancelled) setReportError(err.message);
      } finally {
        if (!cancelled) setLoadingReport(false);
      }
    };
    fetchAll();
    return () => { cancelled = true; };
  }, [baseUrl, resolvedUserId, resolvedAssessmentId]);

  const handleGenerate = useCallback(async () => {
    if (!resolvedUserId || !resolvedAssessmentId) return;
    setGenerating(true);
    setReportError(null);
    try {
      const res = await fetch(`${baseUrl}/api/v1/cosmic/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: resolvedUserId,
          assessment_id: resolvedAssessmentId,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Failed to generate cosmic report');
      }
      const result = await res.json();
      const rep = result?.report || result;
      setCosmicReport(rep);
    } catch (err) {
      setReportError(err.message || 'Failed to generate cosmic report');
    } finally {
      setGenerating(false);
    }
  }, [baseUrl, resolvedUserId, resolvedAssessmentId]);

  if (!data) return null;

  const sections = cosmicReport?.sections || {};
  const hasNarrative = Object.keys(sections).length > 0;
  const eligible = eligibility?.eligible !== false;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center py-4">
        <h1 className="text-2xl font-bold text-indigo-900 flex items-center justify-center gap-2">
          <span>🌌</span> Cosmic Integration Dashboard
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Your unified executive functioning profile across all environments
        </p>
      </div>

      {/* AI narrative — synthesis sections from the cosmic report */}
      {hasNarrative && sections.cosmic_snapshot && (
        <div className="bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-2xl p-6 border border-indigo-100">
          <h3 className="text-lg font-bold text-indigo-900 mb-3 flex items-center gap-2">
            <span>🌌</span> Cosmic Snapshot
          </h3>
          {formatParagraph(sections.cosmic_snapshot)}
        </div>
      )}

      {/* Visual layer */}
      <GalaxyMap data={data} />
      {hasNarrative && sections.galaxy_convergence_map && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🪐</span> Galaxy Convergence Narrative
          </h3>
          {formatParagraph(sections.galaxy_convergence_map)}
        </div>
      )}

      <LoadMatrix data={data} />
      {hasNarrative && sections.cross_domain_load_transfer && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🔁</span> Cross-Domain Load Transfer Analysis
          </h3>
          {formatParagraph(sections.cross_domain_load_transfer)}
        </div>
      )}

      <LoadFlow data={data} />
      {hasNarrative && sections.compensation_patterns && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🛡️</span> Compensation Patterns
          </h3>
          {formatParagraph(sections.compensation_patterns)}
        </div>
      )}

      {hasNarrative && sections.system_wide_sensitivity && (
        <div className="bg-amber-50 rounded-2xl border border-amber-100 p-6">
          <h3 className="text-base font-bold text-amber-900 mb-3 flex items-center gap-2">
            <span>⚠️</span> System-Wide Sensitivity
          </h3>
          {formatParagraph(sections.system_wide_sensitivity)}
        </div>
      )}

      <StabilizersPanel data={data} />
      {hasNarrative && sections.stabilizers_across_universe && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🌱</span> Stabilizers Across Your Universe
          </h3>
          {formatParagraph(sections.stabilizers_across_universe)}
        </div>
      )}

      {hasNarrative && sections.lens_overlay_summary && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🔍</span> Lens Overlay Summary
          </h3>
          {formatParagraph(sections.lens_overlay_summary)}
        </div>
      )}

      <AimsTrack data={data} isCosmic={true} />
      {hasNarrative && sections.cosmic_aims && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🚀</span> Cosmic AIMS Pathway
          </h3>
          {formatParagraph(sections.cosmic_aims)}
        </div>
      )}

      {hasNarrative && sections.long_term_trajectory && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-base font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🛰️</span> Long-Term Trajectory
          </h3>
          {formatParagraph(sections.long_term_trajectory)}
        </div>
      )}

      {hasNarrative && sections.closing_synthesis && (
        <div className="bg-gradient-to-br from-purple-50 via-white to-indigo-50 rounded-2xl p-6 border border-purple-100">
          <h3 className="text-lg font-bold text-purple-900 mb-3 flex items-center gap-2">
            <span>⭐</span> Closing Synthesis
          </h3>
          {formatParagraph(sections.closing_synthesis)}
        </div>
      )}

      {/* Generate cosmic report CTA when we don't yet have one */}
      {!hasNarrative && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100 text-center">
          <h3 className="font-bold text-indigo-900 mb-2">
            {eligible
              ? 'Generate Your Cosmic Integration Report'
              : 'Cosmic Integration Locked'}
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            {eligible
              ? 'Synthesize cross-environmental patterns into a single integrative narrative.'
              : eligibility?.message ||
                'Purchase all four lens reports to unlock the Cosmic Integration synthesis.'}
          </p>
          {eligible && (
            <button
              onClick={handleGenerate}
              disabled={generating || loadingReport}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-60"
            >
              {generating ? 'Generating…' : 'Generate Cosmic Report →'}
            </button>
          )}
          {reportError && (
            <p className="mt-3 text-xs text-red-600">{reportError}</p>
          )}
        </div>
      )}

      {onViewReports && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100 text-center">
          <h3 className="font-bold text-indigo-900 mb-2">
            Explore Your Full AI Reports
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Generate detailed 15-section reports for each life lens, or unlock the
            full Cosmic Integration Report for cross-domain synthesis.
          </p>
          <button
            onClick={onViewReports}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
          >
            View AI Reports →
          </button>
        </div>
      )}
    </div>
  );
};

export default CosmicDashboard;
