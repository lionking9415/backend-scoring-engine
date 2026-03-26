import React, { useState } from 'react';

const Results = ({ data, onRestart }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  const { construct_scores, load_framework, domains, archetype, summary, interpretation } = data;

  const getQuadrantColor = (quadrant) => {
    const colors = {
      'Q1_Aligned_Flow': 'bg-green-100 text-green-800 border-green-300',
      'Q2_Capacity_Strain': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Q3_Overload': 'bg-red-100 text-red-800 border-red-300',
      'Q4_Underutilized': 'bg-blue-100 text-blue-800 border-blue-300',
    };
    return colors[quadrant] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getLoadStateColor = (state) => {
    const colors = {
      'Surplus_Capacity': 'text-green-600',
      'Stable_Capacity': 'text-blue-600',
      'Balanced_Load': 'text-gray-600',
      'Emerging_Strain': 'text-orange-600',
      'Critical_Overload': 'text-red-600',
    };
    return colors[state] || 'text-gray-600';
  };

  const getDomainColor = (classification) => {
    const colors = {
      'Strength': 'bg-green-500',
      'Developed': 'bg-blue-500',
      'Emerging': 'bg-yellow-500',
      'Growth_Edge': 'bg-orange-500',
    };
    return colors[classification] || 'bg-gray-500';
  };

  return (
    <div className="min-h-screen p-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-indigo-900 mb-2">
                Your BEST Galaxy Assessment Results
              </h1>
              <p className="text-gray-600">
                Completed on {new Date(data.metadata?.timestamp).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={onRestart}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all"
            >
              Take Again
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="flex border-b border-gray-200">
            {['overview', 'domains', 'interpretation'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 px-6 py-4 font-medium capitalize transition-all ${
                  activeTab === tab
                    ? 'text-indigo-600 border-b-2 border-indigo-600'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Archetype Card */}
            <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Your Archetype</h2>
                <span className="px-4 py-2 bg-white bg-opacity-20 rounded-full text-sm">
                  {archetype?.confidence || 'Exact Match'}
                </span>
              </div>
              <h3 className="text-4xl font-bold mb-4">
                {archetype?.archetype_id?.replace(/_/g, ' ') || 'N/A'}
              </h3>
              <p className="text-lg opacity-90">
                {archetype?.description || 'No description available'}
              </p>
            </div>

            {/* Scores Grid */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* PEI Score */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-4">
                  PEI Score (Environmental Load)
                </h3>
                <div className="flex items-end justify-between mb-2">
                  <span className="text-5xl font-bold text-indigo-600">
                    {(construct_scores?.PEI_score * 100).toFixed(0)}%
                  </span>
                  <span className="text-sm text-gray-500">
                    Raw: {construct_scores?.PEI_score?.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-indigo-600 h-3 rounded-full transition-all"
                    style={{ width: `${construct_scores?.PEI_score * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* BHP Score */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-4">
                  BHP Score (Internal Capacity)
                </h3>
                <div className="flex items-end justify-between mb-2">
                  <span className="text-5xl font-bold text-purple-600">
                    {(construct_scores?.BHP_score * 100).toFixed(0)}%
                  </span>
                  <span className="text-sm text-gray-500">
                    Raw: {construct_scores?.BHP_score?.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-purple-600 h-3 rounded-full transition-all"
                    style={{ width: `${construct_scores?.BHP_score * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Load Framework */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Load Framework</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <div className={`p-4 rounded-lg border-2 ${getQuadrantColor(load_framework?.quadrant)}`}>
                  <p className="text-sm font-medium mb-1">Quadrant</p>
                  <p className="text-lg font-bold">
                    {load_framework?.quadrant?.replace(/_/g, ' ') || 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg border-2 border-gray-200">
                  <p className="text-sm font-medium text-gray-600 mb-1">Load State</p>
                  <p className={`text-lg font-bold ${getLoadStateColor(load_framework?.load_state)}`}>
                    {load_framework?.load_state?.replace(/_/g, ' ') || 'N/A'}
                  </p>
                </div>
                <div className="p-4 rounded-lg border-2 border-gray-200">
                  <p className="text-sm font-medium text-gray-600 mb-1">Load Balance</p>
                  <p className="text-lg font-bold text-gray-800">
                    {load_framework?.load_balance?.toFixed(3) || 'N/A'}
                  </p>
                </div>
              </div>
            </div>

            {/* Summary */}
            {summary && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Summary</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-green-700 mb-2">Top Strengths</h4>
                    <ul className="space-y-1">
                      {summary.top_strengths?.map((strength, idx) => (
                        <li key={idx} className="text-gray-700">
                          • {strength.replace(/_/g, ' ')}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-orange-700 mb-2">Growth Edges</h4>
                    <ul className="space-y-1">
                      {summary.growth_edges?.map((edge, idx) => (
                        <li key={idx} className="text-gray-700">
                          • {edge.replace(/_/g, ' ')}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Domains Tab */}
        {activeTab === 'domains' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-6">Domain Profiles</h3>
            <div className="space-y-4">
              {domains?.map((domain, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl font-bold text-gray-400">#{domain.rank}</span>
                      <div>
                        <h4 className="font-semibold text-gray-800">
                          {domain.name?.replace(/_/g, ' ')}
                        </h4>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          domain.classification === 'Strength' ? 'bg-green-100 text-green-800' :
                          domain.classification === 'Developed' ? 'bg-blue-100 text-blue-800' :
                          domain.classification === 'Emerging' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-orange-100 text-orange-800'
                        }`}>
                          {domain.classification}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-indigo-600">
                        {(domain.score * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-gray-500">
                        AIMS: {domain.aims_priority || 'N/A'}
                      </p>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getDomainColor(domain.classification)}`}
                      style={{ width: `${domain.score * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interpretation Tab */}
        {activeTab === 'interpretation' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-6">AI Interpretation</h3>
            {interpretation ? (
              <div className="prose max-w-none space-y-6">
                {interpretation.executive_summary && (
                  <div>
                    <h4 className="text-lg font-semibold text-indigo-900 mb-2">Executive Summary</h4>
                    <p className="text-gray-700 leading-relaxed">{interpretation.executive_summary}</p>
                  </div>
                )}
                {interpretation.quadrant_interpretation && (
                  <div>
                    <h4 className="text-lg font-semibold text-indigo-900 mb-2">Quadrant Analysis</h4>
                    <p className="text-gray-700 leading-relaxed">{interpretation.quadrant_interpretation}</p>
                  </div>
                )}
                {interpretation.pei_bhp_interpretation && (
                  <div>
                    <h4 className="text-lg font-semibold text-indigo-900 mb-2">PEI × BHP Balance</h4>
                    <p className="text-gray-700 leading-relaxed">{interpretation.pei_bhp_interpretation}</p>
                  </div>
                )}
                {interpretation.archetype_narrative && (
                  <div>
                    <h4 className="text-lg font-semibold text-indigo-900 mb-2">Your Archetype Story</h4>
                    <p className="text-gray-700 leading-relaxed">{interpretation.archetype_narrative}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-600">No interpretation available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Results;
