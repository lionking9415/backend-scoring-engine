import React from 'react';
import LockedSections from './LockedSections';

// 🔷 1 & 2: Domain plain-language tags + consistent color system
const DOMAIN_META = {
  'Executive Skills & Behavior':       { tag: 'Action & Follow-Through',  color: '#3B82F6', bgClass: 'bg-blue-500' },
  'Cognitive & Motivational Systems':  { tag: 'Focus & Drive',            color: '#8B5CF6', bgClass: 'bg-purple-500' },
  'Emotional & Internal State':        { tag: 'Emotional Regulation',     color: '#F59E0B', bgClass: 'bg-yellow-500' },
  'Environmental Demands':             { tag: 'Life Load',                color: '#EF4444', bgClass: 'bg-red-500' },
};

// 🔷 3: Dynamic load balance label logic — aligned with backend load_state
const getLoadLabel = (loadBalance) => {
  if (!loadBalance) return 'Balanced Under Load';
  const { pei_score, bhp_score, status } = loadBalance;
  if (pei_score != null && bhp_score != null) {
    const diff = bhp_score - pei_score; // BHP - PEI (positive = capacity surplus)
    if (diff >= 0.20) return 'Surplus Capacity';
    if (diff >= 0.05) return 'Stable Capacity';
    if (diff >= -0.04) return 'Balanced Load';
    if (diff >= -0.19) return 'Emerging Strain';
    return 'Critical Overload';
  }
  if (status === 'Balanced') return 'Balanced Load';
  if (status === 'Slightly Imbalanced') return 'Emerging Strain';
  if (status === 'High Load Strain') return 'Critical Overload';
  return 'Emerging Strain';
};

// Helper: get Environmental Demands pressure label
const getEnvPressureLabel = (percentage) => {
  if (percentage >= 80) return 'High Pressure';
  if (percentage >= 60) return 'Moderate Pressure';
  if (percentage >= 40) return 'Mild Pressure';
  return 'Low Pressure';
};

// Check if a domain is Environmental Demands
const isEnvironmentalDomain = (name) => {
  return name === 'Environmental Demands' || name === 'ENVIRONMENTAL_DEMANDS';
};

// Detect if data is full (paid) format vs free scorecard format
const isPaidData = (data) => {
  return !!(data && (data.domains || data.interpretation || data.construct_scores));
};

// Normalize paid data into the dashboard structure
const normalizePaidData = (data) => {
  const archetype = data.archetype || {};
  const loadFramework = data.load_framework || {};
  const summary = data.summary || {};
  const domains = data.domains || [];

  // Build constellation from domains using same grouping as backend SCORECARD_DOMAIN_GROUPS
  const SCORECARD_DOMAIN_GROUPS = {
    'Executive Skills & Behavior': ['EXECUTIVE_FUNCTION_SKILLS', 'BEHAVIORAL_PATTERNS'],
    'Cognitive & Motivational Systems': ['COGNITIVE_CONTROL', 'MOTIVATIONAL_SYSTEMS'],
    'Emotional & Internal State': ['EMOTIONAL_REGULATION', 'INTERNAL_STATE_FACTORS'],
    'Environmental Demands': ['ENVIRONMENTAL_DEMANDS'],
  };
  const profileLookup = {};
  for (const d of domains) {
    profileLookup[d.name] = d.score || 0;
  }
  const finalConstellation = Object.entries(SCORECARD_DOMAIN_GROUPS).map(([groupName, domainKeys]) => {
    const scores = domainKeys.filter(k => k in profileLookup).map(k => profileLookup[k]);
    const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    return { name: groupName, score: avg, percentage: Math.round(avg * 100) };
  });

  const peiScore = data.construct_scores?.PEI_score || loadFramework.pei_score || 0;
  const bhpScore = data.construct_scores?.BHP_score || loadFramework.bhp_score || 0;

  return {
    galaxy_snapshot: {
      archetype_name: (archetype.archetype_id || 'Unknown').replace(/_/g, ' '),
      tagline: archetype.description || '',
    },
    constellation: finalConstellation,
    load_balance: {
      status: loadFramework.load_state?.includes('balanced') ? 'Balanced' : 'Slightly Imbalanced',
      message: 'Your environment and internal capacity are interacting in important ways...',
      executive_summary: data.interpretation?.executive_summary || '',
      pei_score: peiScore,
      bhp_score: bhpScore,
    },
    strengths: (summary.top_strengths || []).map(s => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())),
    growth_edges: (summary.growth_edges || []).map(e => e.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())),
    lens_teasers: null,
    locked_features: null,
    metadata: data.metadata || {},
    // Paid-only fields
    domains: data.domains,
    interpretation: data.interpretation,
    construct_scores: data.construct_scores,
    load_framework: data.load_framework,
  };
};

const ScoreCard = ({ data, onRestart, assessmentId, userEmail }) => {
  const [upgradingFromLens, setUpgradingFromLens] = React.useState(false);
  const [downloadingPdf, setDownloadingPdf] = React.useState(false);
  const [pdfError, setPdfError] = React.useState(null);
  const [expandedSections, setExpandedSections] = React.useState({});

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  // 🔷 9: Unified dashboard — detect paid vs free and normalize
  const isPaid = isPaidData(data);
  const normalized = isPaid ? normalizePaidData(data) : data;

  const {
    galaxy_snapshot,
    constellation,
    load_balance,
    strengths,
    growth_edges,
    lens_teasers,
    locked_features,
    metadata,
  } = normalized;

  // Paid-only data
  const domains = normalized.domains || null;
  const interpretation = normalized.interpretation || null;
  const construct_scores = normalized.construct_scores || null;
  const load_framework = normalized.load_framework || null;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const handleDownloadPdf = async () => {
    if (!assessmentId) {
      setPdfError('No assessment ID available');
      return;
    }
    setDownloadingPdf(true);
    setPdfError(null);

    try {
      const axios = (await import('axios')).default;
      const endpoint = isPaid
        ? `/api/v1/export/pdf/${assessmentId}`
        : `/api/v1/export/scorecard-pdf/${assessmentId}`;

      const response = await axios.get(endpoint, {
        responseType: 'blob',
        timeout: 30000,
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const prefix = isPaid ? 'BEST_Galaxy_FullReport' : 'BEST_Galaxy_ScoreCard';
      link.download = `${prefix}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setDownloadingPdf(false);
    } catch (err) {
      let errorMessage = 'Failed to download PDF';
      if (err.response) {
        errorMessage = `Server error (${err.response.status}): ${err.response.data?.detail || err.response.statusText}`;
      } else if (err.request) {
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        errorMessage = err.message;
      }
      setPdfError(errorMessage);
      setDownloadingPdf(false);
    }
  };

  const handleLensUpgrade = async () => {
    if (!assessmentId) {
      alert('No assessment ID available');
      return;
    }
    if (!userEmail) {
      alert('Please log in to unlock the full report');
      return;
    }
    setUpgradingFromLens(true);

    try {
      const axios = (await import('axios')).default;
      const response = await axios.post('/api/v1/payment/create-checkout', null, {
        params: {
          assessment_id: assessmentId,
          customer_email: userEmail,
          success_url: `${window.location.origin}/success?assessment_id=${assessmentId}`,
          cancel_url: window.location.href
        }
      });

      if (response.data.success && response.data.session) {
        if (response.data.session.checkout_url) {
          window.location.href = response.data.session.checkout_url;
        } else if (response.data.session.error) {
          alert(response.data.session.error);
          setUpgradingFromLens(false);
        }
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create checkout session');
      setUpgradingFromLens(false);
    }
  };

  const loadLabel = getLoadLabel(load_balance);

  const getLoadColor = (label) => {
    if (label === 'Surplus Capacity' || label === 'Stable Capacity') return 'text-green-600 bg-green-50 border-green-200';
    if (label === 'Balanced Load') return 'text-blue-600 bg-blue-50 border-blue-200';
    if (label === 'Emerging Strain') return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getLoadIcon = (label) => {
    if (label === 'Surplus Capacity' || label === 'Stable Capacity') return '✅';
    if (label === 'Balanced Load') return '⚖️';
    if (label === 'Emerging Strain') return '⚠️';
    return '🔴';
  };

  const getDomainColor = (domainName) => {
    const meta = DOMAIN_META[domainName];
    return meta || { tag: '', color: '#6B7280', bgClass: 'bg-gray-500' };
  };

  const getDomainClassColor = (classification, domainName) => {
    if (isEnvironmentalDomain(domainName)) return 'bg-red-500';
    if (classification === 'Strength') return 'bg-green-500';
    if (classification === 'Developed') return 'bg-blue-500';
    if (classification === 'Emerging') return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const getDomainClassLabel = (classification, domainName) => {
    if (isEnvironmentalDomain(domainName)) {
      const score = (domains || []).find(d => isEnvironmentalDomain(d.name))?.score || 0;
      if (score >= 0.8) return 'High Load';
      if (score >= 0.6) return 'Elevated Pressure';
      return 'Moderate Load';
    }
    return classification;
  };

  const lensIcons = {
    PERSONAL_LIFESTYLE: '🌟',
    STUDENT_SUCCESS: '🎓',
    PROFESSIONAL_LEADERSHIP: '💼',
    FAMILY_ECOSYSTEM: '👨‍👩‍👧‍👦',
  };

  // Expandable section helper
  const ExpandableSection = ({ id, title, icon, children, defaultOpen = false }) => {
    const isOpen = expandedSections[id] !== undefined ? expandedSections[id] : defaultOpen;
    return (
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            {icon && <span className="text-xl">{icon}</span>}
            <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          </div>
          <span className={`text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>
        {isOpen && <div className="px-6 pb-6 border-t border-gray-100 pt-4">{children}</div>}
      </div>
    );
  };

  return (
    <div className="min-h-screen p-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── 1. GALAXY SNAPSHOT HEADER ── */}
        <div className="bg-gradient-to-br from-indigo-700 via-purple-700 to-indigo-900 rounded-2xl shadow-xl p-8 text-white text-center">
          {isPaid && (
            <span className="inline-block bg-yellow-400 text-yellow-900 text-xs font-bold px-3 py-1 rounded-full mb-3 uppercase tracking-wider">
              Full Galaxy Report
            </span>
          )}
          <p className="text-indigo-200 text-sm uppercase tracking-widest mb-2">You are</p>
          <h1 className="text-4xl font-extrabold mb-3">
            {galaxy_snapshot?.archetype_name || 'Unknown'}
          </h1>
          <p className="text-lg text-indigo-100 italic mb-4">
            "{galaxy_snapshot?.tagline}"
          </p>
          <p className="text-indigo-200 text-sm mt-2">
            This profile reflects how your internal capacity (BHP) is interacting with your environmental demands (PEI).
          </p>
        </div>

        {/* ── 2. EF CONSTELLATION SCORECARD ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">
            Your Executive Function Constellation
          </h2>
          <div className="ef-constellation-container">
            <div className="space-y-5">
              {constellation?.map((group, idx) => {
                const domainMeta = getDomainColor(group.name);
                const isEnv = isEnvironmentalDomain(group.name);
                return (
                  <div key={idx}>
                    <div className="flex justify-between items-baseline mb-1">
                      <div>
                        <span className="font-semibold" style={{ color: domainMeta.color }}>
                          {isEnv ? `Life Load` : group.name}
                        </span>
                        {domainMeta.tag && (
                          <span className="block text-xs text-gray-500 mt-0.5">
                            {isEnv ? 'Higher = More Pressure on Your System' : domainMeta.tag}
                          </span>
                        )}
                      </div>
                      <span className="text-sm font-bold" style={{ color: domainMeta.color }}>
                        {isEnv ? `${group.percentage}% (${getEnvPressureLabel(group.percentage)})` : `${group.percentage}%`}
                      </span>
                    </div>
                    <div className={`w-full bg-gray-100 rounded-full h-3 relative ${isEnv && group.percentage >= 80 ? 'ring-2 ring-red-300 ring-opacity-75' : ''}`}>
                      {isEnv ? (
                        <div
                          className="h-3 rounded-full transition-all duration-700"
                          style={{
                            width: `${group.percentage}%`,
                            backgroundColor: domainMeta.color,
                            marginLeft: 'auto',
                            float: 'right',
                          }}
                        ></div>
                      ) : (
                        <div
                          className="h-3 rounded-full transition-all duration-700"
                          style={{ width: `${group.percentage}%`, backgroundColor: domainMeta.color }}
                        ></div>
                      )}
                    </div>
                    {isEnv && group.percentage >= 80 && (
                      <div className="flex items-center mt-1">
                        <span className="text-xs text-red-500 font-medium animate-pulse">⚠ Elevated environmental pressure detected</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── 3. LOAD BALANCE SNAPSHOT ── */}
        <div className={`rounded-2xl shadow-md p-6 border-2 ${getLoadColor(loadLabel)}`}>
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">{getLoadIcon(loadLabel)}</span>
            <h2 className="text-xl font-bold">Load Balance: {loadLabel}</h2>
          </div>

          <div className="load-balance-visual-container my-3">
            <div className="flex items-center justify-center space-x-4">
              <div className="text-center">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Internal Capacity (BHP)</div>
                <div className="h-2 rounded-full bg-indigo-400" style={{ width: `${Math.min((load_balance?.bhp_score || 0.5) * 100, 100)}px` }}></div>
                {isPaid && <div className="text-sm font-semibold text-indigo-600 mt-1">{(load_balance?.bhp_score || 0).toFixed(3)}</div>}
              </div>
              <span className="text-gray-400 text-lg">⚖️</span>
              <div className="text-center">
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Environmental Load (PEI)</div>
                <div className="h-2 rounded-full bg-red-400" style={{ width: `${Math.min((load_balance?.pei_score || 0.5) * 100, 100)}px` }}></div>
                {isPaid && <div className="text-sm font-semibold text-red-600 mt-1">{(load_balance?.pei_score || 0).toFixed(3)}</div>}
              </div>
            </div>
          </div>

          <p className="text-gray-600 italic mb-3">
            {load_balance?.message}
          </p>

          {load_balance?.executive_summary && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-gray-700 text-sm leading-relaxed">
                {load_balance.executive_summary}
              </p>
            </div>
          )}
        </div>

        {/* ── 4. STRENGTHS + KEY PRESSURES + GROWTH EDGES ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-green-700 mb-3">✓ Top Strengths</h3>
            <ul className="space-y-2">
              {strengths?.filter(s => !isEnvironmentalDomain(s)).map((s, i) => (
                <li key={i} className="text-gray-700 font-medium">{s}</li>
              ))}
            </ul>
          </div>
          {/* Key Pressures — Environmental Demands separated out */}
          {constellation?.some(g => isEnvironmentalDomain(g.name) && g.percentage >= 60) && (
            <div className="bg-red-50 rounded-2xl shadow-md p-6 border border-red-200">
              <h3 className="font-bold text-red-700 mb-3">⚠ Key Pressures on Your System</h3>
              <ul className="space-y-2">
                {constellation?.filter(g => isEnvironmentalDomain(g.name)).map((g, i) => (
                  <li key={i} className="text-red-700 font-medium">
                    Environmental Demands: {g.percentage}% ({getEnvPressureLabel(g.percentage)})
                  </li>
                ))}
              </ul>
              <p className="text-xs text-red-500 mt-2">This represents external pressure, not internal capacity.</p>
            </div>
          )}
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-orange-600 mb-3">⚡ Growth Edges</h3>
            <ul className="space-y-2">
              {growth_edges?.map((e, i) => (
                <li key={i} className="text-gray-700 font-medium">{e}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── PAID: Domain-by-Domain Scoring (Expandable) ── */}
        {isPaid && domains && (
          <ExpandableSection id="domains" title="Domain-by-Domain Scoring" icon="📊" defaultOpen={true}>
            <div className="space-y-4">
              {/* Internal Capacity Domains */}
              {domains.filter(d => !isEnvironmentalDomain(d.name)).map((domain, idx) => (
                <div key={idx} className="border border-gray-200 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-gray-800">
                      {domain.name.replace(/_/g, ' ')}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${getDomainClassColor(domain.classification, domain.name)}`}>
                      {getDomainClassLabel(domain.classification, domain.name)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex-1 bg-gray-100 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full ${getDomainClassColor(domain.classification, domain.name)}`}
                        style={{ width: `${domain.score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">
                      {(domain.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Rank: #{domain.rank} | AIMS Priority: {domain.aims_priority}
                  </p>
                </div>
              ))}

              {/* Environmental Demands — Visually Separated */}
              {domains.filter(d => isEnvironmentalDomain(d.name)).map((domain, idx) => (
                <div key={`env-${idx}`} className="border-2 border-red-300 rounded-xl p-4 bg-red-50">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <h3 className="font-bold text-red-700">
                        {domain.name.replace(/_/g, ' ')}
                      </h3>
                      <span className="text-xs text-red-500">External Pressure — Not Internal Capacity</span>
                    </div>
                    <span className="px-3 py-1 rounded-full text-white text-xs font-semibold bg-red-500">
                      {getDomainClassLabel(domain.classification, domain.name)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className={`flex-1 bg-gray-100 rounded-full h-3 ${domain.score >= 0.8 ? 'ring-2 ring-red-300' : ''}`}>
                      <div
                        className="h-3 rounded-full bg-red-500"
                        style={{ width: `${domain.score * 100}%`, marginLeft: 'auto', float: 'right' }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold text-red-600">
                      {(domain.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-red-400 mt-2">
                    Rank: #{domain.rank} | AIMS Priority: Monitor & Adjust
                  </p>
                  {domain.score >= 0.8 && (
                    <p className="text-xs text-red-600 font-medium mt-1 animate-pulse">
                      ⚠ High environmental load — this is placing significant pressure on your system
                    </p>
                  )}
                </div>
              ))}
            </div>
          </ExpandableSection>
        )}

        {/* ── PAID: Interpretation Sections (Expandable) ── */}
        {isPaid && interpretation && (
          <>
            {interpretation.quadrant_interpretation && (
              <ExpandableSection id="quadrant" title="Archetype Profile" icon="🌌" defaultOpen={true}>
                <p className="text-gray-700 leading-relaxed">
                  {interpretation.quadrant_interpretation}
                </p>
              </ExpandableSection>
            )}

            {interpretation.load_interpretation && (
              <ExpandableSection id="load-analysis" title="Deep Load Analysis" icon="⚖️" defaultOpen={true}>
                <p className="text-gray-700 leading-relaxed">
                  {interpretation.load_interpretation}
                </p>
              </ExpandableSection>
            )}

            {interpretation.strengths_analysis && (
              <ExpandableSection id="strengths-analysis" title="Strengths Analysis" icon="💪" defaultOpen={true}>
                <p className="text-gray-700 leading-relaxed">
                  {interpretation.strengths_analysis}
                </p>
              </ExpandableSection>
            )}

            {/* Load & Pressure Analysis — separated from Strengths */}
            {load_balance?.pei_score >= 0.6 && (
              <ExpandableSection id="load-pressure" title="Load & Pressure Analysis" icon="🔴" defaultOpen={true}>
                <p className="text-gray-700 leading-relaxed">
                  Your system is currently operating under high environmental load, meaning that
                  external demands are placing sustained pressure on your internal capacity. This
                  level of demand is not a reflection of strength, but rather the intensity of what
                  your system is being required to manage. When environmental load is elevated, even
                  strong internal skills can become strained over time. Adjusting, reducing, or
                  restructuring these external demands will be an important part of restoring balance
                  and supporting long-term performance.
                </p>
              </ExpandableSection>
            )}

            {interpretation.growth_edges_analysis && (
              <ExpandableSection id="growth-analysis" title="Growth Edges Analysis" icon="🌱" defaultOpen={true}>
                <p className="text-gray-700 leading-relaxed">
                  {interpretation.growth_edges_analysis}
                </p>
              </ExpandableSection>
            )}
          </>
        )}

        {/* ── PAID: AIMS Plan (Expandable) ── */}
        {isPaid && interpretation?.aims_plan && (
          <ExpandableSection id="aims" title="AIMS for the BEST™ Plan" icon="🎯" defaultOpen={true}>
            <div className="space-y-4">
              {/* Enforce correct AIMS order: Awareness → Intervention → Mastery → Sustain */}
              {['awareness', 'intervention', 'mastery', 'sustain']
                .filter(phase => interpretation.aims_plan[phase])
                .map((phase) => {
                  const colors = {
                    awareness: 'border-blue-500',
                    intervention: 'border-orange-500',
                    mastery: 'border-purple-500',
                    sustain: 'border-green-500',
                  };
                  return (
                    <div key={phase} className={`border-l-4 ${colors[phase] || 'border-indigo-600'} pl-4`}>
                      <h3 className="font-bold text-gray-800 capitalize mb-2">
                        {phase.replace(/_/g, ' ')}
                      </h3>
                      <p className="text-gray-700 leading-relaxed">{interpretation.aims_plan[phase]}</p>
                    </div>
                  );
                })}
            </div>
          </ExpandableSection>
        )}

        {/* ── PAID: Cosmic Summary ── */}
        {isPaid && interpretation?.cosmic_summary && (
          <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-md p-6 border border-indigo-100">
            <h2 className="text-xl font-bold text-indigo-800 mb-4">Cosmic Summary</h2>
            <p className="text-gray-700 leading-relaxed italic">
              {interpretation.cosmic_summary}
            </p>
          </div>
        )}

        {/* ── 5. FOUR LENS TEASER SECTION (Free only) ── */}
        {!isPaid && lens_teasers && (
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-5">
              Your Profile Across 4 Lenses
            </h2>
            <div className="space-y-5">
              {Object.entries(lens_teasers).map(([key, lens]) => (
                <div key={key} className="border border-gray-200 rounded-xl p-5">
                  <div className="flex items-center space-x-2 mb-3">
                    <span className="text-xl">{lensIcons[key] || '📋'}</span>
                    <h3 className="font-bold text-indigo-900">{lens.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed mb-3">
                    {lens.teaser}
                  </p>
                  <button
                    onClick={handleLensUpgrade}
                    disabled={upgradingFromLens}
                    className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {upgradingFromLens ? '⏳ Processing...' : '🔒 Unlock Full Report →'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── 6. LOCKED SECTIONS (Free only) ── */}
        {!isPaid && (
          <LockedSections
            features={locked_features}
            assessmentId={assessmentId}
            userEmail={userEmail || metadata?.user_id}
          />
        )}

        {/* ── DOWNLOAD PDF ── */}
        <div className="bg-white rounded-2xl shadow-md p-6 text-center">
          <h3 className="text-lg font-bold text-gray-800 mb-3">
            {isPaid ? '📄 Download Your Full Galaxy Report' : '📄 Download Your Free ScoreCard'}
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            {isPaid
              ? 'Save your complete executive function report as a PDF.'
              : 'Save your executive function profile as a PDF for your records.'}
          </p>

          {pdfError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <p className="font-semibold mb-1">Download Failed</p>
              <p>{pdfError}</p>
            </div>
          )}

          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf || !assessmentId}
            className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {downloadingPdf
              ? '⏳ Generating PDF...'
              : isPaid ? 'Download Full Report PDF' : 'Download Free ScoreCard PDF'}
          </button>

          {!assessmentId && (
            <p className="text-xs text-red-600 mt-2">
              Assessment ID missing - cannot download PDF
            </p>
          )}
        </div>

        {/* ── FOOTER ── */}
        <div className="text-center pt-4 pb-8">
          <button
            onClick={onRestart}
            className="text-gray-500 hover:text-gray-700 text-sm underline transition-colors"
          >
            Take Assessment Again
          </button>
        </div>

      </div>
    </div>
  );
};

export default ScoreCard;
