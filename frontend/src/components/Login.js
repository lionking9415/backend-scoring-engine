import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin, onSwitchToSignup, onForgotPassword }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailNotConfirmed, setEmailNotConfirmed] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  const handleResendConfirmation = async () => {
    setResending(true);
    try {
      await axios.post('/api/v1/auth/resend-confirmation', {
        email: email.trim().toLowerCase(),
      });
      setResent(true);
    } catch (_) {
      // endpoint always succeeds
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Mirror backend email normalization so users aren't tripped up by
    // accidental capitalization or trailing whitespace.
    const cleanEmail = email.trim().toLowerCase();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post('/api/v1/auth/login', {
        email: cleanEmail,
        password,
      });

      if (response.data.success) {
        onLogin(response.data.user);
      } else {
        setError('Login failed. Please try again.');
      }
    } catch (err) {
      console.error('Login error:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const code = detail && typeof detail === 'object' ? detail.code : null;
      const message = detail && typeof detail === 'object' ? detail.message : detail;
      if (status === 403 && code === 'email_not_confirmed') {
        setEmailNotConfirmed(true);
        setError(message);
      } else if (status === 401) {
        setError('Invalid email or password');
      } else if (message) {
        setError(message);
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="text-center mb-6">
          <span className="text-4xl mb-3 block">🔐</span>
          <h2 className="text-2xl font-bold text-indigo-900 mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-500 text-sm">
            Log in to access your Galaxy Assessment
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
            {onForgotPassword && (
              <div className="text-right mt-1">
                <button
                  type="button"
                  onClick={onForgotPassword}
                  className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  Forgot password?
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
              {emailNotConfirmed && (
                <div className="mt-2 pt-2 border-t border-red-200">
                  <button
                    type="button"
                    onClick={handleResendConfirmation}
                    disabled={resending || resent}
                    className="text-indigo-600 hover:text-indigo-800 font-semibold text-xs disabled:opacity-50"
                  >
                    {resent ? '✓ Confirmation email resent — check your inbox' : resending ? 'Sending...' : 'Resend confirmation email'}
                  </button>
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToSignup}
              className="text-indigo-600 hover:text-indigo-800 font-semibold"
            >
              Sign Up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
