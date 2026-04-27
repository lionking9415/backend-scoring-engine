import React, { useState, useMemo } from 'react';

// Curated catalog. Each entry can match by:
//   - exact key (lowercased, underscored form)
//   - any keyword in the `keywords` list (substring match on slug)
const STRENGTH_CATALOG = [
  {
    key: 'adaptive_thinking', icon: '🧠', label: 'Adaptive Thinking',
    keywords: ['adaptive', 'flexible_thinking', 'flexibility'],
    where: 'Helps most in: unstructured environments, new situations, problem-solving',
    aims: 'Use as anchor for Intervention stage — apply flexible thinking to break task paralysis',
  },
  {
    key: 'task_initiation', icon: '🚀', label: 'Task Initiation',
    keywords: ['initiation', 'starting', 'task_start'],
    where: 'Helps most in: starting projects, daily routines, meeting deadlines',
    aims: 'Use as anchor for Activation stage — leverage natural start-energy before load builds',
  },
  {
    key: 'emotional_awareness', icon: '💓', label: 'Emotional Awareness',
    keywords: ['emotional', 'emotion', 'feeling', 'self_regulation'],
    where: 'Helps most in: relationships, self-regulation, stress recognition',
    aims: 'Use as anchor for Awareness stage — recognize early signals of system strain',
  },
  {
    key: 'self_awareness', icon: '🔍', label: 'Self-Awareness',
    keywords: ['self_awareness', 'self_monitoring', 'metacognition'],
    where: 'Helps most in: pattern recognition, self-monitoring, growth',
    aims: 'Use as anchor for Mastery stage — track what works and build on it',
  },
  {
    key: 'curiosity', icon: '✨', label: 'Curiosity',
    keywords: ['curiosity', 'engagement', 'interest', 'exploration'],
    where: 'Helps most in: learning, engagement, motivation, exploring solutions',
    aims: 'Use as anchor for all AIMS stages — curiosity drives sustainable engagement',
  },
  {
    key: 'follow_through', icon: '🎯', label: 'Follow-Through',
    keywords: ['follow_through', 'completion', 'persistence', 'reliability'],
    where: 'Helps most in: completing tasks, maintaining routines, reliability',
    aims: 'Use as anchor for Sustain stage — build repeatable systems around this strength',
  },
  {
    key: 'planning', icon: '📋', label: 'Planning',
    keywords: ['planning', 'organization', 'time_management', 'prioritization'],
    where: 'Helps most in: organizing tasks, time management, goal-setting',
    aims: 'Use as anchor for Systemize stage — create structures that reduce decision fatigue',
  },
  {
    key: 'adaptability', icon: '🔄', label: 'Adaptability',
    keywords: ['adaptability', 'recovery', 'resilience'],
    where: 'Helps most in: changing circumstances, unexpected demands, recovery',
    aims: 'Use as anchor for Intervention stage — pivot strategies when primary approach stalls',
  },
  {
    key: 'focus', icon: '🎯', label: 'Focus & Attention',
    keywords: ['focus', 'attention', 'concentration', 'cognitive_control'],
    where: 'Helps most in: deep work, sustained attention, complex tasks',
    aims: 'Use as anchor for Implementation stage — direct focus to highest-leverage actions',
  },
  {
    key: 'motivation', icon: '⚡', label: 'Motivation',
    keywords: ['motivation', 'drive', 'energy', 'motivational'],
    where: 'Helps most in: long-term goals, recovery from setbacks, daily effort',
    aims: 'Use as anchor for Awareness stage — track what energizes and depletes you',
  },
  {
    key: 'social_connection', icon: '🤝', label: 'Social Connection',
    keywords: ['social', 'connection', 'relationship', 'support'],
    where: 'Helps most in: support-seeking, communication, family dynamics',
    aims: 'Use as anchor for Sustain stage — leverage support networks as scaffolding',
  },
  {
    key: 'behavioral_consistency', icon: '🪜', label: 'Behavioral Consistency',
    keywords: ['behavior', 'behavioral', 'consistency', 'routine'],
    where: 'Helps most in: daily routines, habit formation, dependability',
    aims: 'Use as anchor for Mastery stage — repeat what reliably works',
  },
];

const matchStrength = (raw) => {
  const slug = String(raw).toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
  for (const candidate of STRENGTH_CATALOG) {
    if (candidate.key === slug) return candidate;
    if (candidate.keywords.some((kw) => slug.includes(kw))) return candidate;
  }
  return null;
};

const titleCase = (s) =>
  String(s).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const StabilizersPanel = ({ data }) => {
  const [activeStrength, setActiveStrength] = useState(null);

  const displayStrengths = useMemo(() => {
    // Prefer the canonical summary key; fall back to legacy summary_indicators
    const summary = data?.summary || data?.summary_indicators || {};
    const rawList = summary.top_strengths || [];

    const matched = rawList.slice(0, 6).map((s) => {
      const m = matchStrength(s);
      if (m) {
        return { ...m, sourceLabel: titleCase(s) };
      }
      return {
        icon: '⭐',
        label: titleCase(s),
        where: 'Helps maintain stability across environments',
        aims: 'Use as an anchor point in your AIMS plan',
        sourceLabel: titleCase(s),
      };
    });

    // Pull supplementary strengths from applied domains' interpretation block
    const applied = data?.applied_domains || {};
    const appliedStrengths = [];
    ['financial_ef', 'health_ef'].forEach((key) => {
      const interp = applied[key]?.interpretation || {};
      const list = interp.strengths || [];
      list.forEach((s) => {
        const text = typeof s === 'string' ? s : s.label || s.description;
        if (!text) return;
        const m = matchStrength(text);
        const entry = m
          ? { ...m, sourceLabel: titleCase(text) }
          : {
              icon: key === 'financial_ef' ? '💰' : '🏃',
              label: titleCase(text),
              where:
                key === 'financial_ef'
                  ? 'Active in your financial executive functioning'
                  : 'Active in your health & fitness executive functioning',
              aims: 'Use as anchor for Sustain stage — repeat what is already working',
              sourceLabel: titleCase(text),
            };
        appliedStrengths.push(entry);
      });
    });

    // Combine and de-duplicate by label
    const combined = [...matched, ...appliedStrengths];
    const seen = new Set();
    const unique = [];
    for (const s of combined) {
      const k = s.label.toLowerCase();
      if (seen.has(k)) continue;
      seen.add(k);
      unique.push(s);
    }

    if (unique.length === 0) {
      return [
        STRENGTH_CATALOG[0],
        STRENGTH_CATALOG[3],
        STRENGTH_CATALOG[7],
      ];
    }
    return unique.slice(0, 8);
  }, [data]);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
        <span>🌱</span> System Stabilizers
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        Your core strengths that appear across environments — tap to see how to use them
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {displayStrengths.map((s, i) => {
          const isActive = activeStrength === i;
          return (
            <button
              key={`${s.label}-${i}`}
              onClick={() => setActiveStrength(isActive ? null : i)}
              className={`p-3 rounded-xl text-left transition-all border-2 ${
                isActive
                  ? 'border-green-400 bg-green-50 shadow-md'
                  : 'border-gray-100 bg-gray-50 hover:border-green-200 hover:bg-green-50'
              }`}
            >
              <span className="text-2xl block mb-1">{s.icon}</span>
              <span className="text-xs font-bold text-gray-700 block">{s.label}</span>
            </button>
          );
        })}
      </div>

      {activeStrength !== null && displayStrengths[activeStrength] && (
        <div className="mt-4 p-4 bg-green-50 rounded-xl border border-green-100">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">{displayStrengths[activeStrength].icon}</span>
            <span className="font-bold text-green-800 text-sm">
              {displayStrengths[activeStrength].label}
            </span>
          </div>
          <p className="text-xs text-green-700 mb-2">
            {displayStrengths[activeStrength].where}
          </p>
          <div className="bg-white rounded-lg p-2 border border-green-100">
            <p className="text-xs text-green-600 font-semibold">
              AIMS Application: {displayStrengths[activeStrength].aims}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default StabilizersPanel;
