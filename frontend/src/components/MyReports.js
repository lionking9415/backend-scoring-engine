import React, { useEffect, useState } from 'react';
import axios from 'axios';

const MyReports = ({ userEmail, onViewReport, onBack }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReports = async () => {
      if (!userEmail) {
        setError('No user email provided');
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`/api/v1/user/${encodeURIComponent(userEmail)}/reports`);
        if (response.data.success) {
          setReports(response.data.reports);
        } else {
          setError('Failed to load reports');
        }
      } catch (err) {
        console.error('Error fetching reports:', err);
        setError(err.response?.data?.detail || 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [userEmail]);

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getReportTypeBadge = (reportType) => {
    const types = {
      'STUDENT_SUCCESS': { label: 'Student Success', color: 'bg-blue-100 text-blue-800' },
      'PERSONAL_LIFESTYLE': { label: 'Personal/Lifestyle', color: 'bg-purple-100 text-purple-800' },
      'PROFESSIONAL_LEADERSHIP': { label: 'Professional/Leadership', color: 'bg-green-100 text-green-800' },
      'FAMILY_ECOSYSTEM': { label: 'Family/Ecosystem', color: 'bg-pink-100 text-pink-800' },
    };
    const type = types[reportType] || { label: reportType, color: 'bg-gray-100 text-gray-800' };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${type.color}`}>
        {type.label}
      </span>
    );
  };

  const getPaymentBadge = (paymentStatus) => {
    if (paymentStatus === 'paid') {
      return (
        <span className="px-2 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
          ⭐ Full Report
        </span>
      );
    }
    return (
      <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Free ScoreCard
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-indigo-900">My Reports</h1>
              <p className="text-gray-600 mt-1">View all your assessment reports</p>
            </div>
            <button
              onClick={onBack}
              className="text-indigo-600 hover:text-indigo-800 font-semibold transition-colors"
            >
              ← Back to Home
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {reports.length === 0 && !error && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">No Reports Yet</h2>
              <p className="text-gray-600 mb-6">
                You haven't completed any assessments yet. Take your first assessment to get started!
              </p>
              <button
                onClick={onBack}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-xl transition-all duration-200"
              >
                Take Assessment
              </button>
            </div>
          )}

          {reports.length > 0 && (
            <div className="space-y-4">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer bg-white"
                  onClick={() => onViewReport(report.id, report.payment_status)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getPaymentBadge(report.payment_status)}
                        {getReportTypeBadge(report.report_type)}
                      </div>
                      
                      <h3 className="text-lg font-semibold text-gray-800 mb-1">
                        {report.archetype_id ? report.archetype_id.replace(/_/g, ' ') : 'Assessment Report'}
                      </h3>
                      
                      <p className="text-sm text-gray-500">
                        {formatDate(report.created_at)}
                      </p>
                      
                      {report.quadrant && (
                        <p className="text-sm text-gray-600 mt-2">
                          <span className="font-medium">Quadrant:</span> {report.quadrant.replace(/_/g, ' ')}
                        </p>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <button
                        className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm transition-colors"
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewReport(report.id, report.payment_status);
                        }}
                      >
                        View Report →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="text-center text-sm text-gray-600">
          <p>Showing {reports.length} report{reports.length !== 1 ? 's' : ''}</p>
        </div>
      </div>
    </div>
  );
};

export default MyReports;
