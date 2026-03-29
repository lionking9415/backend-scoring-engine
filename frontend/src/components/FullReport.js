import React, { useState } from 'react';

const FullReport = ({ data, onRestart, assessmentId }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No results available</p>
      </div>
    );
  }

  const handleDownloadPdf = async () => {
    if (!assessmentId) {
      alert('No assessment ID available for PDF export');
      return;
    }

    setDownloadingPdf(true);
    
    try {
      const response = await fetch(`/api/v1/export/pdf/${assessmentId}`);
      
      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `BEST_Galaxy_Report_${assessmentId.substring(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('PDF download failed:', error);
      alert('Failed to download PDF. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const {
    metadata,
    construct_scores,
    load_framework,
    domains,
    summary,
    archetype,
    interpretation,
  } = data;

  const getQuadrantColor = (quadrant) => {
    if (quadrant.includes('Q1')) return 'text-green-600 bg-green-50';
    if (quadrant.includes('Q2')) return 'text-yellow-600 bg-yellow-50';
    if (quadrant.includes('Q3')) return 'text-red-600 bg-red-50';
    return 'text-blue-600 bg-blue-50';
  };

  const getDomainColor = (classification) => {
    if (classification === 'Strength') return 'bg-green-500';
    if (classification === 'Developed') return 'bg-blue-500';
    if (classification === 'Emerging') return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 py-8">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="bg-gradient-to-br from-indigo-700 via-purple-700 to-indigo-900 rounded-2xl shadow-xl p-8 text-white mb-6">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-indigo-200 text-sm uppercase tracking-widest mb-2">Full Galaxy Report</p>
              <h1 className="text-4xl font-extrabold mb-2">
                {archetype?.archetype_id?.replace(/_/g, ' ') || 'Your Profile'}
              </h1>
              <p className="text-lg text-indigo-100 italic">
                {archetype?.description}
              </p>
            </div>
            <div className="text-right space-y-3">
              <div>
                <p className="text-indigo-200 text-sm">Report Type</p>
                <p className="font-semibold">{metadata?.report_type?.replace(/_/g, ' ')}</p>
              </div>
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="bg-white text-indigo-700 hover:bg-indigo-50 font-bold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <span>{downloadingPdf ? '⏳' : '📄'}</span>
                <span>{downloadingPdf ? 'Generating...' : 'Download PDF'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-md mb-6 p-2 flex space-x-2">
          {['overview', 'domains', 'interpretation', 'aims'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              {/* Construct Scores */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Construct Scores</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="border border-gray-200 rounded-xl p-4">
                    <p className="text-sm text-gray-600 mb-1">PEI (Environmental Demand)</p>
                    <p className="text-3xl font-bold text-indigo-600">
                      {(construct_scores?.PEI_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="border border-gray-200 rounded-xl p-4">
                    <p className="text-sm text-gray-600 mb-1">BHP (Internal Capacity)</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {(construct_scores?.BHP_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Load Framework */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Load Framework</h2>
                <div className={`rounded-xl p-4 ${getQuadrantColor(load_framework?.quadrant)}`}>
                  <p className="font-bold text-lg mb-2">
                    {load_framework?.quadrant?.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm">
                    Load State: {load_framework?.load_state?.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm">
                    Load Balance: {load_framework?.load_balance?.toFixed(3)}
                  </p>
                </div>
              </div>

              {/* Summary */}
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Summary</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-bold text-green-700 mb-2">✓ Top Strengths</h3>
                    <ul className="space-y-1">
                      {summary?.top_strengths?.map((s, i) => (
                        <li key={i} className="text-gray-700">{s.replace(/_/g, ' ')}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-bold text-orange-600 mb-2">⚡ Growth Edges</h3>
                    <ul className="space-y-1">
                      {summary?.growth_edges?.map((e, i) => (
                        <li key={i} className="text-gray-700">{e.replace(/_/g, ' ')}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Executive Summary */}
              {interpretation?.executive_summary && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Executive Summary</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.executive_summary}
                  </p>
                </div>
              )}
            </>
          )}

          {/* Domains Tab */}
          {activeTab === 'domains' && (
            <div className="bg-white rounded-2xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Domain Profiles</h2>
              <div className="space-y-4">
                {domains?.map((domain, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="font-bold text-gray-800">
                        {domain.name.replace(/_/g, ' ')}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-white text-sm ${getDomainColor(domain.classification)}`}>
                        {domain.classification}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex-1 bg-gray-100 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full ${getDomainColor(domain.classification)}`}
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
              </div>
            </div>
          )}

          {/* Interpretation Tab */}
          {activeTab === 'interpretation' && interpretation && (
            <div className="space-y-6">
              {interpretation.quadrant_interpretation && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Quadrant Analysis</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.quadrant_interpretation}
                  </p>
                </div>
              )}

              {interpretation.load_interpretation && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Load State Analysis</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.load_interpretation}
                  </p>
                </div>
              )}

              {interpretation.pei_bhp_interpretation && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">PEI × BHP Interaction</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.pei_bhp_interpretation}
                  </p>
                </div>
              )}

              {interpretation.strengths_analysis && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Strengths Analysis</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.strengths_analysis}
                  </p>
                </div>
              )}

              {interpretation.growth_edges_analysis && (
                <div className="bg-white rounded-2xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Growth Edges Analysis</h2>
                  <p className="text-gray-700 leading-relaxed">
                    {interpretation.growth_edges_analysis}
                  </p>
                </div>
              )}

              {interpretation.cosmic_summary && (
                <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl shadow-md p-6 border border-indigo-100">
                  <h2 className="text-xl font-bold text-indigo-800 mb-4">Cosmic Summary</h2>
                  <p className="text-gray-700 leading-relaxed italic">
                    {interpretation.cosmic_summary}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* AIMS Tab */}
          {activeTab === 'aims' && interpretation?.aims_plan && (
            <div className="bg-white rounded-2xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">AIMS for the BEST™ Plan</h2>
              <div className="space-y-4">
                {Object.entries(interpretation.aims_plan).map(([phase, content]) => (
                  <div key={phase} className="border-l-4 border-indigo-600 pl-4">
                    <h3 className="font-bold text-gray-800 capitalize mb-2">{phase}</h3>
                    <p className="text-gray-700 leading-relaxed">{content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="text-center pt-8 pb-8">
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

export default FullReport;
