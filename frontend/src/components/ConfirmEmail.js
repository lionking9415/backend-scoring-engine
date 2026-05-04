import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ConfirmEmail = ({ token, onSwitchToLogin }) => {
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('No confirmation token found. Please check your email link.');
      return;
    }

    const confirm = async () => {
      try {
        await axios.post('/api/v1/auth/confirm-email', { token });
        setStatus('success');
      } catch (err) {
        setStatus('error');
        const detail = err.response?.data?.detail;
        const message = detail && typeof detail === 'object' ? detail.message : detail;
        setError(message || 'Failed to confirm email. The link may have expired.');
      }
    };
    confirm();
  }, [token]);

  if (status === 'verifying') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-6 sm:p-8 text-center">
          <div className="animate-spin text-5xl mb-4 inline-block">⏳</div>
          <h2 className="text-2xl font-bold text-indigo-900 mb-3">Confirming Your Email...</h2>
          <p className="text-gray-500 text-sm">Please wait while we verify your email address.</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-6 sm:p-8 text-center">
          <span className="text-5xl mb-4 block">✅</span>
          <h2 className="text-2xl font-bold text-green-700 mb-3">Email Confirmed!</h2>
          <p className="text-gray-600 text-sm mb-6">
            Your email has been verified successfully. You can now log in to your account.
          </p>
          <button
            onClick={onSwitchToLogin}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all shadow-lg hover:shadow-xl"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-6 sm:p-8 text-center">
        <span className="text-5xl mb-4 block">⚠️</span>
        <h2 className="text-2xl font-bold text-red-700 mb-3">Confirmation Failed</h2>
        <p className="text-gray-600 text-sm mb-6">{error}</p>
        <button
          onClick={onSwitchToLogin}
          className="text-indigo-600 hover:text-indigo-800 font-semibold text-sm"
        >
          ← Back to Login
        </button>
      </div>
    </div>
  );
};

export default ConfirmEmail;
