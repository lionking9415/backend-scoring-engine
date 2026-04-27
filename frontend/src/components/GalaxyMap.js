import React, { useState, useMemo } from 'react';

const DOMAINS = [
  { key: 'STUDENT_SUCCESS', label: 'Student', icon: '🎓', angle: 0 },
  { key: 'PERSONAL_LIFESTYLE', label: 'Personal', icon: '🧍', angle: 90 },
  { key: 'PROFESSIONAL_LEADERSHIP', label: 'Professional', icon: '💼', angle: 180 },
  { key: 'FAMILY_ECOSYSTEM', label: 'Family', icon: '👨‍👩‍👧', angle: 270 },
];

const getStabilityColor = (score) => {
  if (score >= 0.6) return { fill: '#22C55E', glow: '#22C55E44', label: 'Stable' };
  if (score >= 0.4) return { fill: '#EAB308', glow: '#EAB30844', label: 'Transitional' };
  return { fill: '#EF4444', glow: '#EF444444', label: 'Strained' };
};

const getLoadRingWidth = (pei) => {
  if (pei >= 0.7) return 6;
  if (pei >= 0.4) return 4;
  return 2;
};

const GalaxyMap = ({ data, lensReports }) => {
  const [activeNode, setActiveNode] = useState(null);

  const archetype = data?.archetype?.archetype_id?.replace(/_/g, ' ') || 'Your Profile';
  const construct = data?.construct_scores || {};
  const overallPei = construct.PEI_score || 0.5;
  const overallBhp = construct.BHP_score || 0.5;

  // Build per-environment data, prioritizing real signal sources in this order:
  //   1. Lens-specific reports if provided (rare — only when 4 reports loaded)
  //   2. cross_domain.lens_profiles from the backend (always available post-Phase 4.5)
  //   3. Approximate from overall scores (last resort)
  const lensData = useMemo(() => {
    const lensProfiles = data?.cross_domain?.lens_profiles || {};

    return DOMAINS.map((d) => {
      // Source 1: per-lens report metadata
      const lensReport = lensReports?.[d.key];
      if (lensReport?.scoring_snapshot) {
        const snap = lensReport.scoring_snapshot;
        return {
          ...d,
          stability: snap.bhp ?? snap.BHP_score ?? overallBhp,
          load: snap.pei ?? snap.PEI_score ?? overallPei,
          source: 'report',
          status: snap.status_band,
        };
      }

      // Source 2: backend-computed cross-domain lens profile
      const profile = lensProfiles[d.key];
      if (profile) {
        return {
          ...d,
          stability: profile.bhp,
          load: profile.pei,
          loadBalance: profile.load_balance,
          status: profile.status,
          source: 'cross_domain',
        };
      }

      // Source 3: fallback to overall scores
      return {
        ...d,
        stability: overallBhp,
        load: overallPei,
        loadBalance: overallBhp - overallPei,
        status: 'transitional',
        source: 'fallback',
      };
    });
  }, [data, lensReports, overallBhp, overallPei]);

  const centerX = 200;
  const centerY = 200;
  const radius = 130;

  const getNodePos = (angleDeg) => {
    const rad = (angleDeg - 90) * (Math.PI / 180);
    return {
      x: centerX + radius * Math.cos(rad),
      y: centerY + radius * Math.sin(rad),
    };
  };

  const activeData = activeNode ? lensData.find((d) => d.key === activeNode) : null;

  return (
    <div className="bg-gradient-to-b from-gray-900 to-indigo-950 rounded-2xl p-6 text-white">
      <h3 className="text-lg font-bold mb-1 flex items-center gap-2">
        <span>🌌</span> Galaxy Convergence Map™
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        How your executive functioning operates across 4 environments
      </p>

      <div className="flex justify-center">
        <svg width="400" height="400" viewBox="0 0 400 400" className="max-w-full">
          {lensData.map((d) => {
            const pos = getNodePos(d.angle);
            const isActive = activeNode === d.key;
            return (
              <line
                key={`line-${d.key}`}
                x1={centerX} y1={centerY}
                x2={pos.x} y2={pos.y}
                stroke={isActive ? '#A78BFA' : '#4B5563'}
                strokeWidth={isActive ? 3 : 1.5}
                strokeDasharray={isActive ? 'none' : '4,4'}
                opacity={isActive ? 1 : 0.4}
              />
            );
          })}

          {lensData.map((d, i) => {
            const next = lensData[(i + 1) % lensData.length];
            const p1 = getNodePos(d.angle);
            const p2 = getNodePos(next.angle);
            return (
              <line
                key={`cross-${i}`}
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="#374151" strokeWidth={1} opacity={0.25}
                strokeDasharray="2,6"
              />
            );
          })}

          <circle cx={centerX} cy={centerY} r={38} fill="#312E81" stroke="#6366F1" strokeWidth={3} />
          <circle cx={centerX} cy={centerY} r={42} fill="none" stroke="#6366F166" strokeWidth={1} />
          <text x={centerX} y={centerY - 6} textAnchor="middle" fill="white" fontSize="20">
            ⭐
          </text>
          <text x={centerX} y={centerY + 14} textAnchor="middle" fill="#C7D2FE" fontSize="8" fontWeight="600">
            {archetype.length > 18 ? archetype.substring(0, 18) + '…' : archetype}
          </text>

          {lensData.map((d) => {
            const pos = getNodePos(d.angle);
            const color = getStabilityColor(d.stability);
            const ringWidth = getLoadRingWidth(d.load);
            const isActive = activeNode === d.key;
            const nodeR = isActive ? 32 : 28;

            return (
              <g
                key={d.key}
                onClick={() => setActiveNode(activeNode === d.key ? null : d.key)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  cx={pos.x} cy={pos.y} r={nodeR + ringWidth}
                  fill="none" stroke={color.fill} strokeWidth={ringWidth}
                  opacity={0.4}
                />
                <circle cx={pos.x} cy={pos.y} r={nodeR + 2} fill={color.glow} />
                <circle
                  cx={pos.x} cy={pos.y} r={nodeR}
                  fill="#1F2937" stroke={color.fill}
                  strokeWidth={isActive ? 3 : 2}
                />
                <text x={pos.x} y={pos.y - 2} textAnchor="middle" fontSize="18" fill="white">
                  {d.icon}
                </text>
                <text x={pos.x} y={pos.y + 14} textAnchor="middle" fontSize="8" fill="#D1D5DB" fontWeight="600">
                  {d.label}
                </text>
                <rect
                  x={pos.x - 22} y={pos.y + nodeR + 8} width={44} height={14}
                  rx={7} fill={color.fill + '33'}
                />
                <text x={pos.x} y={pos.y + nodeR + 18} textAnchor="middle" fontSize="7" fill={color.fill} fontWeight="700">
                  {color.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {activeData && (
        <div className="mt-4 p-4 bg-white bg-opacity-10 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{activeData.icon}</span>
            <span className="font-bold text-sm">
              {activeData.label} Environment
            </span>
            {activeData.status && (
              <span className="ml-auto text-[10px] font-bold uppercase tracking-wide text-gray-300">
                {activeData.status}
              </span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-white bg-opacity-5 rounded-lg p-2">
              <p className="text-xs text-gray-400">Stability</p>
              <p className="font-bold text-sm">{(activeData.stability * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white bg-opacity-5 rounded-lg p-2">
              <p className="text-xs text-gray-400">Load</p>
              <p className="font-bold text-sm">{(activeData.load * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white bg-opacity-5 rounded-lg p-2">
              <p className="text-xs text-gray-400">Balance</p>
              <p className="font-bold text-sm">
                {(((activeData.loadBalance ?? activeData.stability - activeData.load)) * 100).toFixed(0)}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-center gap-6 mt-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500"></span> Stable
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-yellow-500"></span> Transitional
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500"></span> Strained
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-gray-500"></span> Load Transfer
        </span>
      </div>
    </div>
  );
};

export default GalaxyMap;
