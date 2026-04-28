import React, { useState } from 'react';
import axios from 'axios';

const Signup = ({ onSignup, onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [emailExists, setEmailExists] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setEmailExists(false);
    setLoading(true);

    // Match backend normalization so client-side validation accepts the
    // same inputs the server will accept.
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

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Full demographic intake runs in DemographicForm immediately after signup.

    try {
      const response = await axios.post('/api/v1/auth/signup', {
        email: cleanEmail,
        password,
        name: (name || cleanEmail.split('@')[0]).trim(),
      });

      if (response.data.success) {
        onSignup(response.data.user);
      } else {
        setError('Signup failed. Please try again.');
      }
    } catch (err) {
      console.error('Signup error:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      // FastAPI sends our structured detail as an object: {code, message}.
      const code = detail && typeof detail === 'object' ? detail.code : null;
      const message = detail && typeof detail === 'object' ? detail.message : detail;

      if (status === 409 || code === 'email_exists') {
        setEmailExists(true);
        setError(message || 'An account with this email already exists.');
      } else if (status === 400) {
        setError(message || 'Please check your input and try again.');
      } else if (message) {
        setError(message);
      } else {
        setError('Signup failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-6">
          <span className="text-4xl mb-3 block">✨</span>
          <h2 className="text-2xl font-bold text-indigo-900 mb-2">
            Create Your Account
          </h2>
          <p className="text-gray-500 text-sm">
            Join us to unlock your executive function insights
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Full Name (Optional)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

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
            <p className="text-xs text-gray-500 mt-1">At least 6 characters</p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <div>{error}</div>
              {emailExists && (
                <button
                  type="button"
                  onClick={onSwitchToLogin}
                  className="mt-2 text-indigo-600 hover:text-indigo-800 font-semibold underline"
                >
                  Log in instead →
                </button>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            Already have an account?{' '}
            <button
              onClick={onSwitchToLogin}
              className="text-indigo-600 hover:text-indigo-800 font-semibold"
            >
              Log In
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;
