import React, { useState } from 'react';
import axios from 'axios';

// Account-management screen.  Owns the local edit state for the name and
// password forms, posts to the backend, and surfaces inline success/error
// banners.  When the name is changed successfully the parent's `onUpdated`
// callback is fired with the fresh user object so the App-level cache and
// localStorage stay in sync without a full reload.
const Account = ({ user, onUpdated, onBack }) => {
  const [name, setName] = useState(user?.name || '');
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState(null);
  const [nameErr, setNameErr] = useState(null);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [pwMsg, setPwMsg] = useState(null);
  const [pwErr, setPwErr] = useState(null);

  const handleSaveName = async (e) => {
    e.preventDefault();
    setNameMsg(null);
    setNameErr(null);

    const trimmed = name.trim();
    if (!trimmed) {
      setNameErr('Name cannot be empty.');
      return;
    }
    if (trimmed === (user?.name || '').trim()) {
      setNameErr('That is already your current name.');
      return;
    }

    setSavingName(true);
    try {
      const resp = await axios.put('/api/v1/auth/user/name', {
        email: user.email,
        name: trimmed,
      });
      if (resp.data?.user) {
        setNameMsg('Name updated.');
        onUpdated?.(resp.data.user);
      } else {
        setNameErr('Could not update your name.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setNameErr(
        typeof detail === 'string'
          ? detail
          : 'Could not update your name. Please try again.',
      );
    } finally {
      setSavingName(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwMsg(null);
    setPwErr(null);

    if (!currentPassword) {
      setPwErr('Please enter your current password.');
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      setPwErr('New password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwErr('The two new-password fields do not match.');
      return;
    }
    if (newPassword === currentPassword) {
      setPwErr('New password must differ from your current password.');
      return;
    }

    setSavingPassword(true);
    try {
      await axios.post('/api/v1/auth/change-password', {
        email: user.email,
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMsg('Password updated. Use your new password next time you sign in.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setPwErr(
        typeof detail === 'string'
          ? detail
          : 'Could not change your password. Please try again.',
      );
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <div className="bg-gray-50 min-h-[80vh]">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <button
            onClick={onBack}
            className="text-sm text-indigo-600 hover:text-indigo-800 font-semibold"
          >
            &larr; Back
          </button>
          <p className="text-sm font-semibold text-indigo-900 truncate">Account settings</p>
          <span className="w-10 shrink-0" />
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-4 py-6 sm:py-10 space-y-6 sm:space-y-8">
        <header>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Your account</h1>
          <p className="text-sm text-gray-600 mt-1">
            Update your display name or change your password.
          </p>
        </header>

        {/* Read-only profile summary */}
        <section className="bg-white rounded-2xl border border-gray-200 p-5 sm:p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Profile</h2>
          <dl className="grid grid-cols-1 sm:grid-cols-3 gap-y-3 text-sm">
            <dt className="text-gray-500">Email</dt>
            <dd className="sm:col-span-2 text-gray-900 break-all">{user?.email || '—'}</dd>
            <dt className="text-gray-500">Member since</dt>
            <dd className="sm:col-span-2 text-gray-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : '—'}
            </dd>
          </dl>
          <p className="text-xs text-gray-400 mt-4">
            Your email is your account identifier and cannot be changed here.
            Contact support if you need to migrate to a different address.
          </p>
        </section>

        {/* Update name */}
        <section className="bg-white rounded-2xl border border-gray-200 p-5 sm:p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-1">Display name</h2>
          <p className="text-sm text-gray-600 mb-4">
            Shown in your reports and the dashboard greeting.
          </p>
          <form onSubmit={handleSaveName} className="space-y-3">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
              autoComplete="name"
              placeholder="Your name"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 outline-none"
            />
            {nameErr && (
              <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {nameErr}
              </p>
            )}
            {nameMsg && (
              <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                {nameMsg}
              </p>
            )}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={savingName}
                className={`px-5 py-2 rounded-lg font-semibold text-white text-sm transition-colors ${
                  savingName
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
                }`}
              >
                {savingName ? 'Saving…' : 'Save name'}
              </button>
            </div>
          </form>
        </section>

        {/* Change password */}
        <section className="bg-white rounded-2xl border border-gray-200 p-5 sm:p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-1">Password</h2>
          <p className="text-sm text-gray-600 mb-4">
            Choose a new password of at least 6 characters. You will need your
            current password to confirm the change.
          </p>
          <form onSubmit={handleChangePassword} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Current password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                New password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                minLength={6}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Confirm new password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                minLength={6}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-indigo-500 outline-none"
              />
            </div>
            {pwErr && (
              <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {pwErr}
              </p>
            )}
            {pwMsg && (
              <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                {pwMsg}
              </p>
            )}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={savingPassword}
                className={`px-5 py-2 rounded-lg font-semibold text-white text-sm transition-colors ${
                  savingPassword
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
                }`}
              >
                {savingPassword ? 'Saving…' : 'Update password'}
              </button>
            </div>
          </form>
        </section>
      </main>
    </div>
  );
};

export default Account;
