import React, { useState, useMemo } from 'react';

const NODE_DEFS = [
  { key: 'financial', label: 'Financial', icon: '💰', x: 50, y: 50 },
  { key: 'emotional', label: 'Emotional', icon: '💓', x: 200, y: 30 },
  { key: 'academic', label: 'Academic', icon: '🎓', x: 350, y: 50 },
  { key: 'health', label: 'Health', icon: '🏃', x: 125, y: 140 },
  { key: 'work', label: 'Work', icon: '💼', x: 275, y: 140 },
  { key: 'family', label: 'Family', icon: '👨‍👩‍👧', x: 200, y: 210 },
];

// Used only when no backend cross_domain data is available.
const FALLBACK_FLOWS = [
  { from: 'financial', to: 'emotional', strength: 0.5, rationale: 'baseline' },
  { from: 'emotional', to: 'academic', strength: 0.4, rationale: 'baseline' },
  { from: 'health', to: 'work', strength: 0.45, rationale: 'baseline' },
  { from: 'health', to: 'emotional', strength: 0.4, rationale: 'baseline' },
  { from: 'work', to: 'family', strength: 0.3, rationale: 'baseline' },
  { from: 'emotional', to: 'family', strength: 0.4, rationale: 'baseline' },
];

const LoadFlow = ({ data }) => {
  const [activeNode, setActiveNode] = useState(null);

  const { flows, source } = useMemo(() => {
    const real = data?.cross_domain?.flows;
    if (Array.isArray(real) && real.length) {
      return { flows: real, source: 'computed' };
    }
    return { flows: FALLBACK_FLOWS, source: 'fallback' };
  }, [data]);

  const nodeMap = useMemo(() => {
    const m = {};
    NODE_DEFS.forEach((n) => { m[n.key] = n; });
    return m;
  }, []);

  // Filter flows down to nodes we know how to render.
  const renderFlows = useMemo(
    () => flows.filter((f) => nodeMap[f.from] && nodeMap[f.to]),
    [flows, nodeMap]
  );

  const getFlowsForNode = (key) =>
    renderFlows.filter((f) => f.from === key || f.to === key);

  const isFlowActive = (flow) => {
    if (!activeNode) return false;
    return flow.from === activeNode || flow.to === activeNode;
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
        <span>🔗</span> Cross-Domain Load Flow
      </h3>
      <p className="text-xs text-gray-400 mb-1">
        Tap a domain to see where pressure originates and spreads
      </p>
      {source === 'computed' && (
        <p className="text-xs text-purple-500 font-semibold mb-4">
          Computed from your assessment patterns
        </p>
      )}
      {source !== 'computed' && <div className="mb-4" />}

      <div className="flex justify-center">
        <svg width="400" height="250" viewBox="0 0 400 250" className="max-w-full">
          {renderFlows.map((flow, i) => {
            const from = nodeMap[flow.from];
            const to = nodeMap[flow.to];
            const active = isFlowActive(flow);
            const strokeW = 1 + (flow.strength || 0.4) * 4;
            const opacity = active ? 0.85 : activeNode ? 0.08 : 0.25;
            const color = active ? '#7C3AED' : '#9CA3AF';

            return (
              <line
                key={`flow-${i}-${flow.from}-${flow.to}`}
                x1={from.x} y1={from.y}
                x2={to.x} y2={to.y}
                stroke={color}
                strokeWidth={active ? strokeW : 1.5 + (flow.strength || 0.4)}
                opacity={opacity}
                strokeLinecap="round"
              />
            );
          })}

          {NODE_DEFS.map((node) => {
            const isActive = activeNode === node.key;
            const isConnected = activeNode
              ? renderFlows.some(
                  (f) =>
                    (f.from === activeNode && f.to === node.key) ||
                    (f.to === activeNode && f.from === node.key)
                )
              : false;
            const dimmed = activeNode && !isActive && !isConnected;

            return (
              <g
                key={node.key}
                onClick={() => setActiveNode(activeNode === node.key ? null : node.key)}
                style={{ cursor: 'pointer' }}
                opacity={dimmed ? 0.3 : 1}
              >
                <circle
                  cx={node.x} cy={node.y} r={isActive ? 26 : 22}
                  fill={isActive ? '#EDE9FE' : '#F9FAFB'}
                  stroke={isActive ? '#7C3AED' : '#D1D5DB'}
                  strokeWidth={isActive ? 3 : 1.5}
                />
                <text x={node.x} y={node.y + 1} textAnchor="middle" fontSize="16" dominantBaseline="central">
                  {node.icon}
                </text>
                <text
                  x={node.x} y={node.y + 34}
                  textAnchor="middle" fontSize="9"
                  fill={isActive ? '#7C3AED' : '#6B7280'}
                  fontWeight={isActive ? '700' : '500'}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {activeNode && (
        <div className="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-100">
          <p className="text-sm font-semibold text-purple-800 mb-2">
            {nodeMap[activeNode]?.icon} {nodeMap[activeNode]?.label} Load Transfer
          </p>
          <div className="text-xs text-purple-700 space-y-2">
            {getFlowsForNode(activeNode).map((flow, i) => {
              const other = flow.from === activeNode ? flow.to : flow.from;
              const direction = flow.from === activeNode ? 'impacts' : 'influenced by';
              return (
                <div key={i}>
                  <p>
                    {direction === 'impacts' ? '→' : '←'}{' '}
                    <strong>{nodeMap[other]?.label}</strong> ({direction}, strength: {Math.round((flow.strength || 0) * 100)}%)
                  </p>
                  {flow.rationale && flow.rationale !== 'baseline cross-domain coupling' && (
                    <p className="text-purple-500 italic ml-3">{flow.rationale}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default LoadFlow;
