import React from 'react';

const DOMAINS = [
  { key: 'student', lensKey: 'STUDENT_SUCCESS', label: 'Student / Academic', icon: '🎓' },
  { key: 'personal', lensKey: 'PERSONAL_LIFESTYLE', label: 'Personal / Lifestyle', icon: '🧍' },
  { key: 'professional', lensKey: 'PROFESSIONAL_LEADERSHIP', label: 'Professional / Work', icon: '💼' },
  { key: 'family', lensKey: 'FAMILY_ECOSYSTEM', label: 'Family / Relational', icon: '👨‍👩‍👧' },
];

const getStabilityLevel = (bhp) => {
  if (bhp >= 0.6) return { label: 'High', color: '#22C55E', bg: '#F0FDF4' };
  if (bhp >= 0.4) return { label: 'Medium', color: '#EAB308', bg: '#FEFCE8' };
  return { label: 'Low', color: '#EF4444', bg: '#FEF2F2' };
};

const getLoadLevel = (pei) => {
  if (pei >= 0.65) return { label: 'Heavy', color: '#EF4444' };
  if (pei >= 0.4) return { label: 'Medium', color: '#EAB308' };
  return { label: 'Light', color: '#22C55E' };
};

const getStatus = (bhp, pei) => {
  const balance = bhp - pei;
  if (balance >= 0.15) return { label: 'Stable', color: '#22C55E', bg: '#DCFCE7' };
  if (balance >= -0.05) return { label: 'Transitional', color: '#EAB308', bg: '#FEF9C3' };
  if (balance >= -0.2) return { label: 'Strained', color: '#F97316', bg: '#FFF7ED' };
  return { label: 'Saturated', color: '#EF4444', bg: '#FEE2E2' };
};

const LoadMatrix = ({ data }) => {
  const construct = data?.construct_scores || {};
  const pei = construct.PEI_score || 0.5;
  const bhp = construct.BHP_score || 0.5;
  // Support canonical "domains" key, with backward-compat for "domain_profiles".
  const domainProfiles = data?.domains || data?.domain_profiles || [];
  const lensProfiles = data?.cross_domain?.lens_profiles || {};

  const domainMap = {};
  for (const dp of domainProfiles) {
    domainMap[dp.name] = dp.score;
  }

  // Prefer backend-computed lens profiles (Phase 4.5 cross_domain). Fall back
  // to a domain-weighted estimate if the cross_domain layer is unavailable.
  const envData = DOMAINS.map((d) => {
    let envBhp;
    let envPei;
    const lp = lensProfiles[d.lensKey];

    if (lp) {
      envBhp = lp.bhp;
      envPei = lp.pei;
    } else {
      envBhp = bhp;
      envPei = pei;
      if (d.key === 'student') {
        envBhp = (domainMap.COGNITIVE_CONTROL || bhp) * 0.8 + bhp * 0.2;
        envPei = (domainMap.ENVIRONMENTAL_DEMANDS || pei) * 0.7 + pei * 0.3;
      } else if (d.key === 'personal') {
        envBhp = (domainMap.INTERNAL_STATE_FACTORS || bhp) * 0.6 + bhp * 0.4;
        envPei = pei * 1.05;
      } else if (d.key === 'professional') {
        envBhp = (domainMap.EXECUTIVE_FUNCTION_SKILLS || bhp) * 0.7 + bhp * 0.3;
        envPei = pei * 0.95;
      } else if (d.key === 'family') {
        envBhp = (domainMap.EMOTIONAL_REGULATION || bhp) * 0.6 + bhp * 0.4;
        envPei = pei * 1.1;
      }
    }

    envBhp = Math.min(Math.max(envBhp, 0), 1);
    envPei = Math.min(Math.max(envPei, 0), 1);

    return {
      ...d,
      bhp: envBhp,
      pei: envPei,
      stability: getStabilityLevel(envBhp),
      load: getLoadLevel(envPei),
      status: getStatus(envBhp, envPei),
    };
  });

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
        <span>⚖️</span> Load Balance Matrix™
      </h3>
      <p className="text-xs text-gray-400 mb-4">
        Where your system is stable vs strained across environments
      </p>

      {/* Matrix Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-100">
              <th className="text-left py-2 px-3 text-gray-500 font-semibold text-xs">Domain</th>
              <th className="text-center py-2 px-3 text-gray-500 font-semibold text-xs">Stability</th>
              <th className="text-center py-2 px-3 text-gray-500 font-semibold text-xs">Load</th>
              <th className="text-center py-2 px-3 text-gray-500 font-semibold text-xs">Status</th>
            </tr>
          </thead>
          <tbody>
            {envData.map((env) => (
              <tr key={env.key} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{env.icon}</span>
                    <span className="font-medium text-gray-700">{env.label}</span>
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${env.bhp * 100}%`,
                          backgroundColor: env.stability.color,
                        }}
                      />
                    </div>
                    <span
                      className="text-xs font-semibold"
                      style={{ color: env.stability.color }}
                    >
                      {env.stability.label}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${env.pei * 100}%`,
                          backgroundColor: env.load.color,
                        }}
                      />
                    </div>
                    <span
                      className="text-xs font-semibold"
                      style={{ color: env.load.color }}
                    >
                      {env.load.label}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-3 text-center">
                  <span
                    className="inline-block px-3 py-1 rounded-full text-xs font-bold"
                    style={{
                      color: env.status.color,
                      backgroundColor: env.status.bg,
                    }}
                  >
                    {env.status.label}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-xs text-green-600 font-semibold mb-1">Stable Zones</p>
          <p className="text-lg font-bold text-green-700">
            {envData.filter(e => e.status.label === 'Stable').length}
          </p>
        </div>
        <div className="bg-yellow-50 rounded-lg p-3 text-center">
          <p className="text-xs text-yellow-600 font-semibold mb-1">Transitional</p>
          <p className="text-lg font-bold text-yellow-700">
            {envData.filter(e => e.status.label === 'Transitional').length}
          </p>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <p className="text-xs text-red-600 font-semibold mb-1">Strained</p>
          <p className="text-lg font-bold text-red-700">
            {envData.filter(e => ['Strained', 'Saturated'].includes(e.status.label)).length}
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadMatrix;
