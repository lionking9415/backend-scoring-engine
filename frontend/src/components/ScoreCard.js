import React from 'react';
import LockedSections from './LockedSections';

// 🔷 1 & 2: Domain plain-language tags + consistent color system
const DOMAIN_META = {
  'Executive Skills & Behavior':       { tag: 'Action & Follow-Through',  color: '#3B82F6', bgClass: 'bg-blue-500' },
  'Cognitive & Motivational Systems':  { tag: 'Focus & Drive',            color: '#8B5CF6', bgClass: 'bg-purple-500' },
  'Emotional & Internal State':        { tag: 'Emotional Regulation',     color: '#F59E0B', bgClass: 'bg-yellow-500' },
  'Environmental Demands':             { tag: 'Environmental Pressure Load (PEI)', color: '#EF4444', bgClass: 'bg-red-500' },
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
    applied_domains: data.applied_domains || {},
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

const LENS_PRODUCTS = [
  'PERSONAL_LIFESTYLE',
  'STUDENT_SUCCESS',
  'PROFESSIONAL_LEADERSHIP',
  'FAMILY_ECOSYSTEM',
];

const ScoreCard = ({
  data,
  onRestart,
  assessmentId,
  userEmail,
  paidProducts = [],
  onViewCosmic,
  onViewAIReports,
}) => {
  const [upgradingFromLens, setUpgradingFromLens] = React.useState(false);
  const [unlockingLens, setUnlockingLens] = React.useState(null); // SKU currently being unlocked
  const [downloadingPdf, setDownloadingPdf] = React.useState(false);
  const [pdfError, setPdfError] = React.useState(null);
  const [expandedSections, setExpandedSections] = React.useState({});
  const [selectedLens, setSelectedLens] = React.useState(null);

  // 🔷 9: Unified dashboard — detect paid vs free and normalize.
  // Trust the server-provided paidProducts list first; fall back to the
  // legacy data-shape heuristic only if the prop wasn't passed (e.g. cached
  // localStorage entry). All hooks below MUST run on every render — they
  // sit above the early-return guard.
  const hasAnyUnlock = (paidProducts || []).length > 0;
  const cosmicUnlocked = (paidProducts || []).includes('COSMIC_BUNDLE');
  const unlockedLenses = LENS_PRODUCTS.filter((l) =>
    (paidProducts || []).includes(l) || cosmicUnlocked,
  );
  const isLensUnlocked = React.useCallback((lensKey) => {
    if (lensKey === 'FULL_GALAXY') return cosmicUnlocked;
    return cosmicUnlocked || (paidProducts || []).includes(lensKey);
  }, [cosmicUnlocked, paidProducts]);

  const isPaid = hasAnyUnlock ? true : isPaidData(data);

  // Auto-select the first unlocked lens once we know what's paid.
  React.useEffect(() => {
    if (isPaid && !selectedLens) {
      const firstUnlocked = ['PERSONAL_LIFESTYLE', 'STUDENT_SUCCESS', 'PROFESSIONAL_LEADERSHIP', 'FAMILY_ECOSYSTEM', 'FULL_GALAXY']
        .find(isLensUnlocked);
      if (firstUnlocked) setSelectedLens(firstUnlocked);
    }
  }, [isPaid, selectedLens, isLensUnlocked]);

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  const normalized = isPaid ? normalizePaidData(data) : data;

  const {
    galaxy_snapshot,
    constellation,
    load_balance,
    applied_domains,
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
    // For paid reports, require lens selection AND ensure that lens is unlocked
    if (isPaid && !selectedLens) {
      setPdfError('Please select a report lens before downloading');
      return;
    }
    if (isPaid && selectedLens && !isLensUnlocked(selectedLens)) {
      setPdfError(`The ${selectedLens.replace(/_/g, ' ')} lens is locked. Please unlock it first.`);
      return;
    }
    setDownloadingPdf(true);
    setPdfError(null);

    try {
      const axios = (await import('axios')).default;
      
      // Build endpoint with lens parameter for paid reports
      let endpoint;
      if (isPaid) {
        endpoint = `/api/v1/export/pdf/${assessmentId}`;
        if (selectedLens) {
          endpoint += `?lens=${selectedLens}`;
        }
      } else {
        endpoint = `/api/v1/export/scorecard-pdf/${assessmentId}`;
      }

      const response = await axios.get(endpoint, {
        responseType: 'blob',
        timeout: 30000,
        headers: userEmail ? { 'X-User-Email': userEmail } : undefined,
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Include lens name in filename for paid reports
      let filename;
      if (isPaid && selectedLens) {
        const lensName = selectedLens.replace(/_/g, '_');
        filename = `BEST_Galaxy_${lensName}_${new Date().toISOString().split('T')[0]}.pdf`;
      } else {
        const prefix = isPaid ? 'BEST_Galaxy_FullReport' : 'BEST_Galaxy_ScoreCard';
        filename = `${prefix}_${new Date().toISOString().split('T')[0]}.pdf`;
      }
      
      link.download = filename;
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

  // Initiate Stripe checkout for a specific lens SKU. FULL_GALAXY maps to
  // the COSMIC_BUNDLE product since there is no standalone "FULL_GALAXY" SKU.
  const handleUnlockLens = async (lensKey) => {
    if (!assessmentId) {
      alert('No assessment ID available');
      return;
    }
    if (!userEmail) {
      alert('Please log in to unlock this lens');
      return;
    }
    const product = lensKey === 'FULL_GALAXY' ? 'COSMIC_BUNDLE' : lensKey;
    setUnlockingLens(product);
    try {
      const axios = (await import('axios')).default;
      const response = await axios.post('/api/v1/payment/create-checkout', null, {
        params: {
          assessment_id: assessmentId,
          customer_email: userEmail,
          product,
          success_url: `${window.location.origin}/success?assessment_id=${assessmentId}&product=${product}`,
          cancel_url: window.location.href,
        },
      });
      if (response.data?.success && response.data?.session?.checkout_url) {
        window.location.href = response.data.session.checkout_url;
        return;
      }
      const msg = response.data?.session?.error || 'Failed to start checkout. Please try again.';
      alert(msg);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Checkout request failed.';
      alert(`Could not start checkout: ${msg}`);
    } finally {
      setUnlockingLens(null);
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
                          {isEnv ? '⚠️ Environmental Pressure Load (PEI)' : group.name}
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
                    <div className={`w-full bg-gray-100 rounded-full h-3 relative ${isEnv && group.percentage >= 60 ? 'ring-2 ring-red-300 ring-opacity-75' : ''}`}
                      style={isEnv ? { boxShadow: group.percentage >= 60 ? '0 0 8px rgba(239, 68, 68, 0.4)' : 'none' } : {}}
                    >
                      {isEnv ? (
                        <div
                          className="h-3 rounded-full transition-all duration-700"
                          style={{
                            width: `${group.percentage}%`,
                            background: `linear-gradient(to left, #FCA5A5, #EF4444, #B91C1C)`,
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
                    {isEnv && group.percentage >= 60 && (
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

        {/* ── 3. LOAD BALANCE — TEETER-TOTTER VISUALIZATION ── */}
        <div className="mt-6">
        {(() => {
          const bhp = load_balance?.bhp_score || 0;
          const pei = load_balance?.pei_score || 0;
          const delta = pei - bhp;
          const absDelta = Math.abs(delta);
          // Tilt angle: slight 4°, moderate 8°, high 13°, max 15°
          let tiltAngle = 0;
          let tiltLabel = 'Balanced';
          if (absDelta < 0.01) { tiltAngle = 0; tiltLabel = 'Balanced'; }
          else if (absDelta < 0.05) { tiltAngle = 4; tiltLabel = delta > 0 ? 'Balanced Under Load' : 'Capacity Supported'; }
          else if (absDelta < 0.12) { tiltAngle = 8; tiltLabel = delta > 0 ? 'Capacity Strain' : 'Capacity Dominant'; }
          else { tiltAngle = 13; tiltLabel = delta > 0 ? 'Critical Overload' : 'Capacity Dominant'; }
          // Direction: positive delta = PEI heavier = clockwise tilt (right side down)
          const beamRotation = delta > 0 ? tiltAngle : -tiltAngle;
          // Delta color
          const deltaColor = delta > 0.01 ? '#DC2626' : delta < -0.01 ? '#2563EB' : '#6B7280';
          const deltaSign = delta > 0 ? '+' : '';
          // Pressure level chip
          const pressureLevel = absDelta < 0.01 ? 'None' : absDelta < 0.05 ? 'Mild' : absDelta < 0.12 ? 'Moderate' : 'High';

          return (
            <div className="bg-white rounded-2xl p-7 border border-gray-200" style={{ boxShadow: '0 8px 24px rgba(31, 41, 55, 0.08)', maxWidth: '920px', margin: '0 auto' }}>
              {/* Header Row */}
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="#D4A62A"><path d="M12 3L2 12h3v8h14v-8h3L12 3zm0 2.84L18.16 11H17v7H7v-7H5.84L12 5.84z" opacity=".3"/><path d="M12 1L1 11h3v10h16V11h3L12 1zm6 18H6v-8.17l6-5.34 6 5.34V19z"/></svg>
                  <h2 className="text-lg font-bold" style={{ color: '#2563EB' }}>Load Balance: {loadLabel}</h2>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full" style={{ background: '#EEF4FF', color: '#2563EB' }}>
                  {tiltLabel}
                </span>
              </div>

              {/* Teeter-Totter Visualization */}
              <div className="flex flex-col items-center" style={{ minHeight: '180px' }}>
                {/* Labels above beam */}
                <div className="flex justify-between w-full" style={{ maxWidth: '560px' }}>
                  <div className="text-center">
                    <div className="text-xs font-bold tracking-wide" style={{ color: '#6B7280' }}>INTERNAL CAPACITY (BHP)</div>
                    <div className="mx-auto mt-1 rounded-full" style={{ width: '48px', height: '4px', background: '#8B5CF6' }}></div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs font-bold tracking-wide" style={{ color: '#6B7280' }}>ENVIRONMENTAL LOAD (PEI)</div>
                    <div className="mx-auto mt-1 rounded-full" style={{ width: '48px', height: '4px', background: '#F87171' }}></div>
                  </div>
                </div>

                {/* Beam + Nodes */}
                <div className="relative flex items-center justify-center mt-4" style={{ width: '100%', maxWidth: '560px', height: '80px' }}>
                  {/* BHP Node (left) */}
                  <div className="absolute flex flex-col items-center justify-center rounded-full text-white"
                    style={{
                      width: '52px', height: '52px', background: '#8B5CF6',
                      left: '0', top: '50%',
                      transform: `translateY(-50%) translateY(${Math.sin(beamRotation * Math.PI / 180) * -60}px)`,
                      zIndex: 2, transition: 'transform 0.5s ease',
                    }}>
                    <span style={{ fontSize: '10px', fontWeight: 600 }}>BHP</span>
                    <span style={{ fontSize: '14px', fontWeight: 700 }}>{bhp.toFixed(3)}</span>
                  </div>

                  {/* Beam */}
                  <div style={{
                    width: '340px', height: '8px', borderRadius: '999px', background: '#C9D2E3',
                    transform: `rotate(${beamRotation}deg)`,
                    transition: 'transform 0.5s ease',
                  }}></div>

                  {/* PEI Node (right) */}
                  <div className="absolute flex flex-col items-center justify-center rounded-full text-white"
                    style={{
                      width: '52px', height: '52px', background: '#F87171',
                      right: '0', top: '50%',
                      transform: `translateY(-50%) translateY(${Math.sin(beamRotation * Math.PI / 180) * 60}px)`,
                      zIndex: 2, transition: 'transform 0.5s ease',
                    }}>
                    <span style={{ fontSize: '10px', fontWeight: 600 }}>PEI</span>
                    <span style={{ fontSize: '14px', fontWeight: 700 }}>{pei.toFixed(3)}</span>
                  </div>
                </div>

                {/* Pivot triangle */}
                <div style={{ width: 0, height: 0, borderLeft: '17px solid transparent', borderRight: '17px solid transparent', borderBottom: '26px solid #D4A62A', marginTop: '-4px' }}></div>

                {/* Delta indicator */}
                <div className="text-center mt-2">
                  <span className="text-sm font-semibold" style={{ color: deltaColor }}>
                    Load Difference: {deltaSign}{delta.toFixed(3)}
                  </span>
                  <p className="text-xs mt-0.5" style={{ color: '#6B7280' }}>
                    {absDelta < 0.01 ? 'Environmental Load Matches Capacity' :
                     delta > 0 ? 'Environmental Load Exceeds Capacity' : 'Internal Capacity Exceeds Load'}
                  </p>
                </div>
              </div>

              {/* Interpretation line */}
              <p className="text-center italic mt-3 mb-4" style={{ fontSize: '16px', color: '#4B5563' }}>
                {load_balance?.message || 'Your environment and internal capacity are interacting in important ways...'}
              </p>

              {/* Divider */}
              <div style={{ width: '100%', height: '1px', background: '#E5E7EB', margin: '0 0 18px 0' }}></div>

              {/* Classification chips */}
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="inline-flex items-center gap-1 text-xs rounded-full border px-3 py-1" style={{ background: '#F8FAFC', borderColor: '#E5E7EB' }}>
                  <span className="font-semibold" style={{ color: '#6B7280' }}>Load State:</span>
                  <span className="font-bold" style={{ color: '#111827' }}>{loadLabel}</span>
                </span>
                <span className="inline-flex items-center gap-1 text-xs rounded-full border px-3 py-1" style={{ background: '#F8FAFC', borderColor: '#E5E7EB' }}>
                  <span className="font-semibold" style={{ color: '#6B7280' }}>System Status:</span>
                  <span className="font-bold" style={{ color: '#111827' }}>{tiltLabel}</span>
                </span>
                <span className="inline-flex items-center gap-1 text-xs rounded-full border px-3 py-1" style={{ background: '#F8FAFC', borderColor: '#E5E7EB' }}>
                  <span className="font-semibold" style={{ color: '#6B7280' }}>Pressure Level:</span>
                  <span className="font-bold" style={{ color: '#111827' }}>{pressureLevel}</span>
                </span>
              </div>

              {/* Executive summary paragraph */}
              {load_balance?.executive_summary && (
                <p style={{ fontSize: '15px', lineHeight: 1.7, color: '#374151' }}>
                  {load_balance.executive_summary}
                </p>
              )}
            </div>
          );
        })()}
        </div>

        {/* ── 4. STRENGTHS + KEY PRESSURES + GROWTH EDGES ── */}
        <div className={`grid grid-cols-1 gap-4 ${constellation?.some(g => isEnvironmentalDomain(g.name) && g.percentage >= 60) ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
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

        {/* ── 5. APPLIED EXECUTIVE FUNCTIONING DOMAINS (Phase 4) ── */}
        {applied_domains && (applied_domains.financial_ef || applied_domains.health_ef) && (
          <div className="mt-6">
            <h2 className="text-lg font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="text-xl">💼</span> Applied Executive Functioning Domains
            </h2>
            <p className="text-xs text-gray-400 mb-4">How your executive functioning expresses in everyday living</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['financial_ef', 'health_ef'].map(key => {
                const ad = applied_domains[key];
                if (!ad) return null;
                const isFinancial = key === 'financial_ef';
                const icon = isFinancial ? '💰' : '🏃';
                const accentColor = isFinancial ? '#8B5CF6' : '#10B981';
                const accentBg = isFinancial ? 'bg-purple-50 border-purple-200' : 'bg-emerald-50 border-emerald-200';
                const accentText = isFinancial ? 'text-purple-700' : 'text-emerald-700';
                const accentBar = isFinancial ? 'bg-purple-500' : 'bg-emerald-500';
                const scorePercent = Math.min(100, Math.max(0, ad.domain_score || 50));

                return (
                  <div key={key} className={`rounded-xl shadow-sm p-4 border ${accentBg}`}>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className={`font-bold ${accentText} text-base flex items-center gap-2`}>
                          <span className="text-xl">{icon}</span>
                          {ad.domain_name || (isFinancial ? 'Financial Executive Functioning Profile™' : 'Health & Fitness Executive Functioning Profile™')}
                        </h3>
                      </div>
                      <span
                        className="px-3 py-1 rounded-full text-white text-xs font-semibold whitespace-nowrap"
                        style={{ backgroundColor: ad.status_band_color || '#6B7280' }}
                      >
                        {ad.status_band || 'N/A'}
                      </span>
                    </div>

                    {/* Domain Score Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Domain Score</span>
                        <span className="font-bold" style={{ color: accentColor }}>{scorePercent.toFixed(0)}/100</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className={`h-2.5 rounded-full ${accentBar}`}
                          style={{ width: `${scorePercent}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* BHP / PEI Mini Row */}
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div className="bg-white rounded-lg p-2 text-center shadow-sm">
                        <div className="text-xs text-gray-500">Internal Capacity (BHP)</div>
                        <div className="text-lg font-bold text-blue-600">{(ad.bhp || 0).toFixed(1)}</div>
                      </div>
                      <div className="bg-white rounded-lg p-2 text-center shadow-sm">
                        <div className="text-xs text-gray-500">External Pressure (PEI)</div>
                        <div className="text-lg font-bold text-red-500">{(ad.pei || 0).toFixed(1)}</div>
                      </div>
                    </div>

                    {/* Mini Load Balance Visualization */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>BHP</span>
                        <span>Load Balance</span>
                        <span>PEI</span>
                      </div>
                      <div className="relative w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="absolute left-0 top-0 h-full bg-blue-400 rounded-l-full"
                          style={{ width: `${Math.min(100, ((ad.bhp || 50) / ((ad.bhp || 50) + (ad.pei || 50))) * 100)}%` }}
                        ></div>
                        <div
                          className="absolute right-0 top-0 h-full bg-red-400 rounded-r-full"
                          style={{ width: `${Math.min(100, ((ad.pei || 50) / ((ad.bhp || 50) + (ad.pei || 50))) * 100)}%` }}
                        ></div>
                        <div className="absolute left-1/2 top-0 h-full w-0.5 bg-gray-600 transform -translate-x-1/2"></div>
                      </div>
                    </div>

                    {/* Interpretation (When Stable / When Loaded) */}
                    {ad.interpretation && (
                      <div className="space-y-2 mb-3">
                        {ad.interpretation.when_stable && (
                          <div className="text-xs">
                            <span className="font-semibold text-green-600">When Stable: </span>
                            <span className="text-gray-600">{ad.interpretation.when_stable}</span>
                          </div>
                        )}
                        {ad.interpretation.when_loaded && (
                          <div className="text-xs">
                            <span className="font-semibold text-orange-600">Under Load: </span>
                            <span className="text-gray-600">{ad.interpretation.when_loaded}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Risk Flags */}
                    {ad.active_flags && ad.active_flags.length > 0 && (
                      <div className="mb-3">
                        <div className="text-xs font-semibold text-gray-600 mb-1">Risk Flags:</div>
                        <div className="flex flex-wrap gap-1">
                          {ad.active_flags.map((flag, i) => (
                            <span key={i} className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                              ⚠ {flag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AIMS Targets (collapsible for paid, teaser for free) */}
                    {isPaid && ad.aims_targets && ad.aims_targets.length > 0 && (
                      <div>
                        <div className="text-xs font-semibold text-gray-600 mb-1">AIMS Targets:</div>
                        <div className="space-y-1">
                          {ad.aims_targets.map((target, i) => (
                            <div key={i} className="flex items-start gap-1 text-xs">
                              <span className="font-semibold" style={{ color: accentColor, minWidth: '80px' }}>
                                {target.phase}:
                              </span>
                              <span className="text-gray-600">{target.target}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {!isPaid && (
                      <div className="mt-3 pt-2 border-t border-gray-200">
                        <button
                          onClick={handleLensUpgrade}
                          disabled={upgradingFromLens}
                          className="w-full text-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors disabled:opacity-50"
                        >
                          {upgradingFromLens ? '⏳ Processing...' : '🔍 View Details — Unlock Full Report →'}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

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

        {/* ── PAID: Applied EF Domains Detail (Expandable) ── */}
        {isPaid && applied_domains && (applied_domains.financial_ef || applied_domains.health_ef) && (
          <ExpandableSection id="applied-domains" title="Applied EF Domain Analysis" icon="💼" defaultOpen={true}>
            <div className="space-y-6">
              {['financial_ef', 'health_ef'].map(key => {
                const ad = (data.applied_domains || applied_domains || {})[key];
                if (!ad) return null;
                const isFinancial = key === 'financial_ef';
                const accentColor = isFinancial ? '#8B5CF6' : '#10B981';
                const accentBorder = isFinancial ? 'border-purple-300' : 'border-emerald-300';
                const accentBg = isFinancial ? 'bg-purple-50' : 'bg-emerald-50';
                const accentText = isFinancial ? 'text-purple-700' : 'text-emerald-700';
                const icon = isFinancial ? '💰' : '🏃';
                const scorePercent = Math.min(100, Math.max(0, ad.domain_score || 50));
                const subvars = ad.subvariables || {};
                const flags = ad.flags || {};
                const aims = ad.aims_targets || [];
                const interp = ad.interpretation || {};

                const activeFlags = Object.entries(flags)
                  .filter(([, v]) => v && v.triggered)
                  .map(([, v]) => v.description);

                return (
                  <div key={key} className={`border-2 ${accentBorder} rounded-xl p-5 ${accentBg}`}>
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                      <h3 className={`font-bold ${accentText} text-lg flex items-center gap-2`}>
                        <span>{icon}</span>
                        {ad.domain_name || (isFinancial ? 'Financial Executive Functioning Profile™' : 'Health & Fitness Executive Functioning Profile™')}
                      </h3>
                      <span
                        className="px-3 py-1 rounded-full text-white text-sm font-semibold"
                        style={{ backgroundColor: ad.status_band_color || '#6B7280' }}
                      >
                        {ad.status_band || 'N/A'}
                      </span>
                    </div>

                    {/* Score + BHP/PEI/LB Row */}
                    <div className="grid grid-cols-4 gap-3 mb-4">
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <div className="text-xs text-gray-500">Domain Score</div>
                        <div className="text-2xl font-bold" style={{ color: accentColor }}>{scorePercent.toFixed(0)}</div>
                        <div className="text-xs text-gray-400">/100</div>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <div className="text-xs text-gray-500">BHP (Capacity)</div>
                        <div className="text-2xl font-bold text-blue-600">{(ad.bhp || 0).toFixed(1)}</div>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <div className="text-xs text-gray-500">PEI (Pressure)</div>
                        <div className="text-2xl font-bold text-red-500">{(ad.pei || 0).toFixed(1)}</div>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <div className="text-xs text-gray-500">Load Balance</div>
                        <div className={`text-2xl font-bold ${(ad.load_balance || 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                          {(ad.load_balance || 0) >= 0 ? '+' : ''}{(ad.load_balance || 0).toFixed(1)}
                        </div>
                      </div>
                    </div>

                    {/* Interpretation */}
                    {interp.when_stable && (
                      <div className="bg-white rounded-lg p-3 mb-2 shadow-sm">
                        <span className="font-semibold text-green-600 text-sm">When Stable: </span>
                        <span className="text-gray-700 text-sm">{interp.when_stable}</span>
                      </div>
                    )}
                    {interp.when_loaded && (
                      <div className="bg-white rounded-lg p-3 mb-2 shadow-sm">
                        <span className="font-semibold text-orange-600 text-sm">Under Load: </span>
                        <span className="text-gray-700 text-sm">{interp.when_loaded}</span>
                      </div>
                    )}

                    {/* Domain Interpretation Narrative (Block 5) */}
                    {interp.domain_narrative && (
                      <div className="bg-white rounded-lg p-3 mb-3 shadow-sm border-l-4" style={{ borderLeftColor: accentColor }}>
                        <span className="font-semibold text-gray-700 text-sm">Pattern Analysis: </span>
                        <span className="text-gray-600 text-sm">{interp.domain_narrative}</span>
                        {interp.strain_source && (
                          <span className={`ml-2 inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                            interp.strain_source === 'capacity-driven' ? 'bg-green-100 text-green-700' :
                            interp.strain_source === 'load-driven' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>
                            {interp.strain_source}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Subvariables Breakdown */}
                    {Object.keys(subvars).length > 0 && (
                      <div className="mb-3">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Subvariable Breakdown</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {Object.entries(subvars).map(([varName, varScore]) => (
                            <div key={varName} className="bg-white rounded-lg px-3 py-2 shadow-sm flex items-center justify-between">
                              <span className="text-xs text-gray-600">
                                {varName.replace(/_/g, ' ').replace(/^(financial|health)\s/, '').replace(/\b\w/g, c => c.toUpperCase())}
                              </span>
                              <div className="flex items-center gap-2">
                                <div className="w-16 bg-gray-200 rounded-full h-1.5">
                                  <div
                                    className="h-1.5 rounded-full"
                                    style={{ width: `${Math.min(100, varScore)}%`, backgroundColor: accentColor }}
                                  ></div>
                                </div>
                                <span className="text-xs font-semibold" style={{ color: accentColor, minWidth: '28px', textAlign: 'right' }}>
                                  {varScore.toFixed(0)}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risk Flags */}
                    {activeFlags.length > 0 && (
                      <div className="mb-3">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Risk Flags</h4>
                        <div className="flex flex-wrap gap-2">
                          {activeFlags.map((flag, i) => (
                            <span key={i} className="px-3 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                              ⚠ {flag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AIMS Targets */}
                    {aims.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">AIMS Targets</h4>
                        <div className="space-y-1">
                          {aims.map((target, i) => (
                            <div key={i} className="bg-white rounded-lg px-3 py-2 shadow-sm flex items-start gap-2">
                              <span className="font-semibold text-xs whitespace-nowrap" style={{ color: accentColor, minWidth: '85px' }}>
                                {target.phase}:
                              </span>
                              <span className="text-xs text-gray-600">{target.target}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
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

        {/* ── REPORT LENS SELECTION (Paid) + DOWNLOAD PDF ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          {isPaid && (
            <>
              <h2 className="text-xl font-bold text-gray-800 mb-2 text-center">Select Your Data Report Lens</h2>
              <p className="text-gray-500 text-sm text-center mb-1">
                Your assessment data can be interpreted through multiple lenses. Choose an unlocked lens to download, or unlock another.
              </p>
              <p className="text-gray-400 text-xs text-center mb-5 italic">
                These are <span className="font-semibold text-indigo-600">structured data PDFs</span> — charts, scores, and AIMS targets.
                Looking for the AI-written interpretation? Generate it from <span className="font-semibold">AI Reports</span> below.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                {[
                  { key: 'PERSONAL_LIFESTYLE', icon: '🔵', title: 'Personal / Lifestyle', desc: 'Understand how your executive functioning shows up in your daily life — from routines and organization to energy, consistency, and self-management.' },
                  { key: 'STUDENT_SUCCESS', icon: '🟣', title: 'Student Success', desc: 'Explore how your executive functioning impacts learning, focus, organization, and academic performance.' },
                  { key: 'PROFESSIONAL_LEADERSHIP', icon: '🔴', title: 'Professional / Leadership', desc: 'Discover how your executive functioning influences productivity, decision-making, leadership, and performance under pressure.' },
                  { key: 'FAMILY_ECOSYSTEM', icon: '🟡', title: 'Family Ecosystem', desc: 'Gain insight into how your executive functioning operates within your relationships and family environment.' },
                  { key: 'FULL_GALAXY', icon: '🌠', title: 'Full Galaxy Report', desc: 'Experience the complete picture of your executive functioning system across all areas of life — personal, academic, professional, and family lenses unified.' },
                ].map(lens => {
                  const unlocked = isLensUnlocked(lens.key);
                  const isSelected = selectedLens === lens.key;
                  const productSku = lens.key === 'FULL_GALAXY' ? 'COSMIC_BUNDLE' : lens.key;
                  const isUnlockingThis = unlockingLens === productSku;

                  // UNLOCKED tile — selectable for download
                  if (unlocked) {
                    return (
                      <div
                        key={lens.key}
                        onClick={() => setSelectedLens(lens.key)}
                        className={`relative border-2 rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${
                          isSelected
                            ? 'border-indigo-600 bg-indigo-100 ring-2 ring-indigo-300'
                            : 'border-indigo-200 bg-indigo-50/30 hover:border-indigo-400'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {isSelected && <span className="text-sm">✓</span>}
                          <span className="text-lg">{lens.icon}</span>
                          <h3 className={`font-bold text-sm ${
                            isSelected ? 'text-indigo-900' : 'text-gray-800'
                          }`}>{lens.title}</h3>
                          <span className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">
                            UNLOCKED
                          </span>
                        </div>
                        <p className={`text-xs leading-relaxed ${
                          isSelected ? 'text-indigo-700' : 'text-gray-600'
                        }`}>{lens.desc}</p>
                      </div>
                    );
                  }

                  // LOCKED tile — clicking starts Stripe checkout for this SKU
                  return (
                    <button
                      key={lens.key}
                      type="button"
                      onClick={() => handleUnlockLens(lens.key)}
                      disabled={isUnlockingThis || !!unlockingLens}
                      className="relative text-left border-2 border-dashed border-amber-300 bg-amber-50/40 hover:bg-amber-50 rounded-xl p-4 transition-all hover:shadow-md disabled:opacity-60 disabled:cursor-wait"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg opacity-60">{lens.icon}</span>
                        <h3 className="font-bold text-sm text-gray-700">{lens.title}</h3>
                        <span className="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200 flex items-center gap-1">
                          <span>🔒</span> LOCKED
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed text-gray-500 mb-2">{lens.desc}</p>
                      <div className="text-xs font-semibold text-amber-700">
                        {isUnlockingThis ? 'Opening checkout…' : `Click to unlock ${lens.key === 'FULL_GALAXY' ? 'the Cosmic Bundle' : 'this lens'}`}
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="border-t border-gray-200 pt-5" />
            </>
          )}

          <div className="text-center">
            <h3 className="text-lg font-bold text-gray-800 mb-1">
              {isPaid ? '📊 Download Your Data Report (PDF)' : '📄 Download Your Free ScoreCard'}
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              {isPaid
                ? 'Charts, subvariable bars, applied-domain tables, and AIMS targets — derived directly from the scoring engine.'
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
              disabled={downloadingPdf || !assessmentId || (isPaid && !selectedLens)}
              className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloadingPdf
                ? '⏳ Generating PDF...'
                : isPaid && selectedLens
                ? `Download ${selectedLens.replace(/_/g, ' ').replace(/FULL GALAXY/, 'Full Galaxy')} Data Report`
                : isPaid
                ? 'Select a Lens to Download'
                : 'Download Free ScoreCard PDF'}
            </button>

            {!assessmentId && (
              <p className="text-xs text-red-600 mt-2">
                Assessment ID missing - cannot download PDF
              </p>
            )}
          </div>
        </div>

        {/* ── COSMIC & AI REPORTS NAV ──
            These are PREMIUM features. Free users see locked tiles that
            scroll the page back to the upgrade CTA so the gate is obvious;
            paid users get full nav buttons.
        */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 px-2">
          {onViewCosmic && (
            cosmicUnlocked ? (
              <button
                onClick={onViewCosmic}
                className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-gray-900 to-indigo-950 text-white hover:from-gray-800 hover:to-indigo-900 transition-all shadow-lg"
              >
                <span className="text-2xl">🌌</span>
                <div className="text-left">
                  <span className="font-bold text-sm block">Cosmic Dashboard</span>
                  <span className="text-xs text-gray-300">Galaxy Map, Load Matrix & more</span>
                </div>
              </button>
            ) : (
              <div
                className="flex items-center gap-3 p-4 rounded-xl bg-gray-100 border-2 border-dashed border-gray-300 text-gray-500 cursor-not-allowed"
                title="Unlock the Cosmic Bundle to view this dashboard"
              >
                <span className="text-2xl">🔒</span>
                <div className="text-left">
                  <span className="font-bold text-sm block">Cosmic Dashboard</span>
                  <span className="text-xs">Locked — purchase the Cosmic Bundle</span>
                </div>
              </div>
            )
          )}
          {onViewAIReports && (
            unlockedLenses.length > 0 ? (
              <button
                onClick={onViewAIReports}
                className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
              >
                <span className="text-2xl">✍️</span>
                <div className="text-left">
                  <span className="font-bold text-sm block">AI Narrative Reports</span>
                  <span className="text-xs text-indigo-200">
                    {unlockedLenses.length === 1
                      ? '15-section AI interpretation · 1 lens'
                      : `15-section AI interpretation · ${unlockedLenses.length} lenses`}
                  </span>
                </div>
              </button>
            ) : (
              <div
                className="flex items-center gap-3 p-4 rounded-xl bg-gray-100 border-2 border-dashed border-gray-300 text-gray-500 cursor-not-allowed"
                title="Unlock at least one lens to view AI narrative reports"
              >
                <span className="text-2xl">🔒</span>
                <div className="text-left">
                  <span className="font-bold text-sm block">AI Narrative Reports</span>
                  <span className="text-xs">15-section AI interpretation — unlock any lens to begin</span>
                </div>
              </div>
            )
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
