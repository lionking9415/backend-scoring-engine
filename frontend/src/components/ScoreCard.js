import React from 'react';
import LockedSections from './LockedSections';

const ScoreCard = ({ data, onRestart }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  const {
    galaxy_snapshot,
    constellation,
    load_balance,
    strengths,
    growth_edges,
    lens_teasers,
    locked_features,
  } = data;

  const getLoadColor = (status) => {
    if (status === 'Balanced') return 'text-green-600 bg-green-50 border-green-200';
    if (status === 'Slightly Imbalanced') return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getLoadIcon = (status) => {
    if (status === 'Balanced') return '⚖️';
    if (status === 'Slightly Imbalanced') return '⚠️';
    return '🔴';
  };

  const getBarColor = (pct) => {
    if (pct >= 75) return 'bg-green-500';
    if (pct >= 50) return 'bg-blue-500';
    if (pct >= 35) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const lensIcons = {
    PERSONAL_LIFESTYLE: '🌟',
    STUDENT_SUCCESS: '🎓',
    PROFESSIONAL_LEADERSHIP: '💼',
    FAMILY_ECOSYSTEM: '👨‍👩‍👧‍👦',
  };

  return (
    <div className="min-h-screen p-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── 1. GALAXY SNAPSHOT HEADER ── */}
        <div className="bg-gradient-to-br from-indigo-700 via-purple-700 to-indigo-900 rounded-2xl shadow-xl p-8 text-white text-center">
          <p className="text-indigo-200 text-sm uppercase tracking-widest mb-2">You are</p>
          <h1 className="text-4xl font-extrabold mb-3">
            {galaxy_snapshot?.archetype_name || 'Unknown'}
          </h1>
          <p className="text-lg text-indigo-100 italic">
            "{galaxy_snapshot?.tagline}"
          </p>
        </div>

        {/* ── 2. EF CONSTELLATION SCORECARD ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">
            Your Executive Function Constellation
          </h2>
          <div className="space-y-4">
            {constellation?.map((group, idx) => (
              <div key={idx}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-gray-700">{group.name}</span>
                  <span className="text-sm font-semibold text-gray-500">{group.percentage}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-700 ${getBarColor(group.percentage)}`}
                    style={{ width: `${group.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── 3. LOAD BALANCE SNAPSHOT ── */}
        <div className={`rounded-2xl shadow-md p-6 border-2 ${getLoadColor(load_balance?.status)}`}>
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">{getLoadIcon(load_balance?.status)}</span>
            <h2 className="text-xl font-bold">Load Balance: {load_balance?.status}</h2>
          </div>
          <p className="text-gray-600 italic">
            {load_balance?.message}
          </p>
        </div>

        {/* ── 4. STRENGTHS + GROWTH EDGES ── */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-green-700 mb-3">✓ Top Strengths</h3>
            <ul className="space-y-2">
              {strengths?.map((s, i) => (
                <li key={i} className="text-gray-700 font-medium">{s}</li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="font-bold text-orange-600 mb-3">⚡ Growth Edges</h3>
            <ul className="space-y-2">
              {growth_edges?.map((e, i) => (
                <li key={i} className="text-gray-700 font-medium">{e}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── 5. FOUR LENS TEASER SECTION ── */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-5">
            Your Profile Across 4 Lenses
          </h2>
          <div className="space-y-5">
            {lens_teasers && Object.entries(lens_teasers).map(([key, lens]) => (
              <div key={key} className="border border-gray-200 rounded-xl p-5">
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-xl">{lensIcons[key] || '📋'}</span>
                  <h3 className="font-bold text-indigo-900">{lens.title}</h3>
                </div>
                <p className="text-gray-600 leading-relaxed mb-3">
                  {lens.teaser}
                </p>
                <button className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold transition-colors">
                  🔒 Unlock Full Report →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ── 6. LOCKED SECTIONS ── */}
        <LockedSections features={locked_features} />

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
