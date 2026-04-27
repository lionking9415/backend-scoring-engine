import React, { useState, useMemo } from 'react';

const STAGE_DEFINITIONS = [
  {
    key: 'A',
    label: 'Awareness & Activation',
    icon: '🅰️',
    color: '#6366F1',
    bg: '#EEF2FF',
    description: 'Recognize when demands begin to overlap. Identify early signals: delay, fatigue, reduced follow-through.',
    fallbackActions: [
      'Notice when multiple responsibilities compete for attention',
      'Identify your personal early-warning signals',
      'Track which environments trigger the most strain',
    ],
  },
  {
    key: 'I',
    label: 'Intervention & Implementation',
    icon: '🅸',
    color: '#8B5CF6',
    bg: '#F5F3FF',
    description: 'Break tasks into single-step actions. Use external structure tools. Focus on one domain at a time.',
    fallbackActions: [
      'Break large tasks into smallest possible next steps',
      'Use visual planners, checklists, or time blocks',
      'Introduce one simple awareness habit',
      'Stabilize one anchor (sleep, hydration, or movement)',
    ],
  },
  {
    key: 'M',
    label: 'Mastery & Integration',
    icon: '🅼',
    color: '#7C3AED',
    bg: '#FAF5FF',
    description: 'Practice consistency under low-pressure conditions first. Gradually apply strategies during higher-demand periods.',
    fallbackActions: [
      'Practice new strategies when load is low',
      'Gradually extend to higher-demand situations',
      'Track patterns, not perfection',
      'Reinforce what works across environments',
    ],
  },
  {
    key: 'S',
    label: 'Sustain / Scaffold / Systemize',
    icon: '🆂',
    color: '#4F46E5',
    bg: '#EEF2FF',
    description: 'Build repeatable life-wide systems, not isolated habits. Reduce decision fatigue through pre-structure.',
    fallbackActions: [
      'Create weekly planning resets',
      'Build predictable daily routines',
      'Reduce decision fatigue through pre-planned schedules',
      'Align environment with capacity across all domains',
    ],
  },
];

// Map a backend AIMS phase string to one of the 4 stage keys.
const phaseKeyOf = (phase) => {
  if (!phase) return null;
  const p = String(phase).toLowerCase();
  if (p.includes('aware') || p.includes('activ')) return 'A';
  if (p.includes('interv') || p.includes('implement')) return 'I';
  if (p.includes('master') || p.includes('integr')) return 'M';
  if (p.includes('sustain') || p.includes('scaffold') || p.includes('system')) return 'S';
  return null;
};

const AimsTrack = ({ data, isCosmic = false }) => {
  const [activeStage, setActiveStage] = useState(null);

  // Pull personalized AIMS targets from backend output:
  //   data.applied_domains.financial_ef.aims_targets
  //   data.applied_domains.health_ef.aims_targets
  // Each entry has shape { phase, focus, action }.
  const personalizedActions = useMemo(() => {
    const buckets = { A: [], I: [], M: [], S: [] };
    const applied = data?.applied_domains || {};

    const collect = (domainKey, label) => {
      const ad = applied[domainKey];
      if (!ad?.aims_targets) return;
      ad.aims_targets.forEach((t) => {
        const k = phaseKeyOf(t.phase);
        if (!k) return;
        buckets[k].push({
          source: label,
          focus: t.focus || '',
          action: t.action || t.target || '',
        });
      });
    };

    collect('financial_ef', 'Financial');
    collect('health_ef', 'Health & Fitness');

    return buckets;
  }, [data]);

  // Pull cross-domain compensation patterns to enrich Mastery/Sustain stages.
  const compensationActions = useMemo(() => {
    const patterns = data?.cross_domain?.compensation_patterns || [];
    return patterns.slice(0, 2).map((p) => ({
      source: 'Cross-domain',
      focus: p.stabilizer,
      action: p.narrative,
    }));
  }, [data]);

  // Build the final stages with personalization layered in.
  const stages = useMemo(() => {
    return STAGE_DEFINITIONS.map((stage) => {
      const personalized = personalizedActions[stage.key] || [];
      let actions = personalized.map((a) =>
        a.source ? `${a.source} — ${a.focus}: ${a.action}` : a.action
      );

      if ((stage.key === 'M' || stage.key === 'S') && compensationActions.length) {
        actions = [
          ...actions,
          ...compensationActions.map((a) => `${a.source}: ${a.action}`),
        ];
      }

      // Always keep at least 2 fallback actions so the panel never looks empty.
      if (actions.length < 2) {
        actions = [...actions, ...stage.fallbackActions.slice(0, 4 - actions.length)];
      }

      return {
        ...stage,
        actions,
        personalizedCount: personalized.length,
      };
    });
  }, [personalizedActions, compensationActions]);

  const totalPersonalized = stages.reduce((n, s) => n + s.personalizedCount, 0);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
        <span>🚀</span> AIMS for the BEST™ {isCosmic ? '— Cosmic Pathway' : '— Your Journey'}
      </h3>
      <p className="text-xs text-gray-400 mb-1">
        {isCosmic
          ? 'Life-wide intervention pathway based on cross-domain patterns'
          : 'Your personalized intervention pathway — tap each stage to explore'
        }
      </p>
      {totalPersonalized > 0 && (
        <p className="text-xs text-indigo-500 font-semibold mb-5">
          {totalPersonalized} personalized {totalPersonalized === 1 ? 'target' : 'targets'} from your assessment
        </p>
      )}
      {totalPersonalized === 0 && <div className="mb-5" />}

      <div className="relative">
        <div className="absolute top-8 left-8 right-8 h-1 bg-gray-200 rounded-full z-0">
          <div
            className="h-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
            style={{
              width: activeStage !== null
                ? `${((activeStage + 1) / stages.length) * 100}%`
                : '0%',
            }}
          />
        </div>

        <div className="relative z-10 flex justify-between">
          {stages.map((stage, i) => {
            const isActive = activeStage === i;
            const isPast = activeStage !== null && i <= activeStage;
            return (
              <button
                key={stage.key}
                onClick={() => setActiveStage(isActive ? null : i)}
                className="flex flex-col items-center group"
                style={{ width: `${100 / stages.length}%` }}
              >
                <div
                  className={`w-16 h-16 rounded-2xl flex items-center justify-center text-2xl transition-all border-3 ${
                    isActive
                      ? 'shadow-lg scale-110 border-2'
                      : isPast
                        ? 'shadow-md border-2'
                        : 'shadow-sm border border-gray-200 group-hover:shadow-md group-hover:scale-105'
                  }`}
                  style={{
                    backgroundColor: isActive || isPast ? stage.bg : '#F9FAFB',
                    borderColor: isActive || isPast ? stage.color : '#E5E7EB',
                  }}
                >
                  <span className="text-xl font-black" style={{ color: stage.color }}>
                    {stage.key}
                  </span>
                </div>
                <span
                  className={`mt-2 text-xs font-semibold text-center leading-tight ${
                    isActive ? 'text-gray-800' : 'text-gray-500'
                  }`}
                >
                  {stage.label.split(' & ').map((part, j) => (
                    <React.Fragment key={j}>
                      {part}{j === 0 && stage.label.includes('&') ? ' &' : ''}
                      {j === 0 && stage.label.includes('&') && <br />}
                    </React.Fragment>
                  ))}
                </span>
                {stage.personalizedCount > 0 && (
                  <span
                    className="mt-1 text-[10px] font-bold rounded-full px-1.5"
                    style={{ backgroundColor: stage.bg, color: stage.color }}
                  >
                    {stage.personalizedCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {activeStage !== null && (
        <div
          className="mt-6 p-5 rounded-xl border-2 transition-all"
          style={{
            backgroundColor: stages[activeStage].bg,
            borderColor: stages[activeStage].color + '44',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <span
              className="text-xl font-black"
              style={{ color: stages[activeStage].color }}
            >
              {stages[activeStage].key}
            </span>
            <h4 className="font-bold text-gray-800">
              {stages[activeStage].label}
            </h4>
            {stages[activeStage].personalizedCount > 0 && (
              <span
                className="ml-auto text-[10px] font-bold rounded-full px-2 py-0.5"
                style={{
                  backgroundColor: stages[activeStage].color + '22',
                  color: stages[activeStage].color,
                }}
              >
                {stages[activeStage].personalizedCount} personalized
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-4">
            {stages[activeStage].description}
          </p>
          <div className="space-y-2">
            {stages[activeStage].actions.map((action, i) => (
              <div key={i} className="flex items-start gap-2">
                <span
                  className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mt-0.5"
                  style={{ backgroundColor: stages[activeStage].color }}
                >
                  {i + 1}
                </span>
                <span className="text-sm text-gray-700">{action}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AimsTrack;
