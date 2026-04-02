import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ScoreCard from './ScoreCard';

const PaymentSuccess = () => {
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      const params = new URLSearchParams(window.location.search);
      const assessmentId = params.get('assessment_id');

      if (!assessmentId) {
        setError('No assessment ID provided');
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`/api/v1/results/${assessmentId}`);
        
        if (response.data.success) {
          setReportData(response.data.data);
        } else {
          setError('Failed to load report');
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your full report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.href = '/'}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-lg"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  if (reportData) {
    const params = new URLSearchParams(window.location.search);
    const assessmentId = params.get('assessment_id');
    // 🔷 9: Use unified ScoreCard dashboard — paid data auto-detected and expanded
    return <ScoreCard data={reportData} onRestart={() => window.location.href = '/'} assessmentId={assessmentId} />;
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-gray-600">No report data available</p>
    </div>
  );
};

export default PaymentSuccess;
