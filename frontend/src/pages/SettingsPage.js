import React, { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { User, Lock, Globe, Loader2 } from 'lucide-react';

export default function SettingsPage() {
  const { t, language, switchLanguage } = useLanguage();
  const { user, updateUser } = useAuth();
  const { put, loading } = useApi();

  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || ''
  });
  const [passwordForm, setPasswordForm] = useState({ password: '' });

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    try {
      const updated = await put('/api/auth/profile', profileForm);
      updateUser(updated);
      toast.success(t.settings.profileUpdated);
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    try {
      await put('/api/auth/profile', passwordForm);
      toast.success(t.settings.profileUpdated);
      setPasswordForm({ password: '' });
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn" data-testid="settings-page">
      <h1 className="text-3xl font-bold text-text-primary">{t.settings.title}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <div className="card" data-testid="profile-settings">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <User size={20} />
              {t.settings.profile}
            </h2>
          </div>
          <form onSubmit={handleUpdateProfile} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">{t.users.name}</label>
              <input
                type="text"
                value={profileForm.name}
                onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                className="input-field"
                required
                data-testid="profile-name-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">{t.users.email}</label>
              <input
                type="email"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                className="input-field"
                required
                data-testid="profile-email-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">{t.users.phone}</label>
              <input
                type="tel"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                className="input-field"
                required
                data-testid="profile-phone-input"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2"
              data-testid="update-profile-button"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              {t.settings.updateProfile}
            </button>
          </form>
        </div>

        {/* Password Settings */}
        <div className="card" data-testid="password-settings">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <Lock size={20} />
              {t.settings.changePassword}
            </h2>
          </div>
          <form onSubmit={handleChangePassword} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">{t.settings.newPassword}</label>
              <input
                type="password"
                value={passwordForm.password}
                onChange={(e) => setPasswordForm({ password: e.target.value })}
                className="input-field"
                required
                minLength={6}
                data-testid="new-password-input"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !passwordForm.password}
              className="btn-primary w-full flex items-center justify-center gap-2"
              data-testid="change-password-button"
            >
              {loading && <Loader2 size={18} className="animate-spin" />}
              {t.settings.changePassword}
            </button>
          </form>
        </div>

        {/* Language Settings */}
        <div className="card" data-testid="language-settings">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <Globe size={20} />
              {t.settings.language}
            </h2>
          </div>
          <div className="p-6">
            <div className="flex gap-4">
              <button
                onClick={() => switchLanguage('uz')}
                className={`flex-1 py-4 rounded-lg font-medium transition-colors ${
                  language === 'uz'
                    ? 'bg-primary text-black'
                    : 'bg-background-subtle text-text-secondary hover:bg-gray-100'
                }`}
                data-testid="settings-lang-uz"
              >
                O'zbekcha
              </button>
              <button
                onClick={() => switchLanguage('ru')}
                className={`flex-1 py-4 rounded-lg font-medium transition-colors ${
                  language === 'ru'
                    ? 'bg-primary text-black'
                    : 'bg-background-subtle text-text-secondary hover:bg-gray-100'
                }`}
                data-testid="settings-lang-ru"
              >
                Русский
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
