import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { toast } from 'sonner';
import { Eye, EyeOff, Globe, Loader2, MessageCircle } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, isTelegram, telegramLinkRequired, telegramUser, linkTelegramAccount } = useAuth();
  const { t, language, switchLanguage } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (telegramLinkRequired) {
        // Linking Telegram account to existing CRM user
        await linkTelegramAccount(email, password);
        toast.success(t.auth?.telegramLinked || 'Telegram account linked successfully!');
      } else {
        // Normal login
        await login(email, password);
        toast.success(t.auth.welcome);
      }
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.auth.loginError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left side - Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 lg:px-16 bg-white">
        <div className="max-w-md w-full mx-auto">
          {/* Language switcher */}
          <div className="flex items-center gap-2 mb-12">
            <Globe size={18} className="text-text-secondary" />
            <button
              onClick={() => switchLanguage('uz')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                language === 'uz'
                  ? 'bg-primary text-black'
                  : 'text-text-secondary hover:bg-gray-100'
              }`}
              data-testid="login-lang-uz"
            >
              UZ
            </button>
            <button
              onClick={() => switchLanguage('ru')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                language === 'ru'
                  ? 'bg-primary text-black'
                  : 'text-text-secondary hover:bg-gray-100'
              }`}
              data-testid="login-lang-ru"
            >
              RU
            </button>
          </div>

          {/* Logo */}
          <h1 className="text-4xl font-bold mb-2" data-testid="login-logo">
            <span className="text-primary">School</span>CRM
          </h1>
          <p className="text-text-secondary mb-10">{t.auth.welcome}</p>

          {/* Telegram Link Notice */}
          {telegramLinkRequired && telegramUser && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg" data-testid="telegram-link-notice">
              <div className="flex items-start gap-3">
                <MessageCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-900">
                    {t.auth?.telegramLinkTitle || 'Link Your Telegram Account'}
                  </p>
                  <p className="text-sm text-blue-700 mt-1">
                    {t.auth?.telegramLinkDesc || `Welcome, ${telegramUser.first_name}! Enter your CRM credentials to link your Telegram account.`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                {t.auth.email}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="admin@crm.local"
                required
                data-testid="login-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                {t.auth.password}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-12"
                  placeholder="••••••••"
                  required
                  data-testid="login-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                  data-testid="toggle-password-visibility"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2"
              data-testid="login-submit-button"
            >
              {loading && <Loader2 size={20} className="animate-spin" />}
              {telegramLinkRequired 
                ? (t.auth?.linkAccount || 'Link Account') 
                : t.auth.loginButton}
            </button>
          </form>

          {/* Telegram indicator */}
          {isTelegram && (
            <p className="text-center text-sm text-text-muted mt-4" data-testid="telegram-indicator">
              <MessageCircle className="inline w-4 h-4 mr-1" />
              {t.auth?.openedViaTelegram || 'Opened via Telegram'}
            </p>
          )}
        </div>
      </div>

      {/* Right side - Image (hidden on mobile and in Telegram) */}
      {!isTelegram && (
        <div
          className="hidden lg:block lg:w-1/2 bg-secondary relative overflow-hidden"
          data-testid="login-hero"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-secondary via-secondary to-primary/20" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center px-12">
              <div className="w-40 h-40 rounded-2xl mx-auto mb-8 flex items-center justify-center overflow-hidden bg-black">
                <img 
                  src="/images/logo.jpg" 
                  alt="SchoolCRM" 
                  className="w-full h-full object-cover"
                />
              </div>
              <h2 className="text-3xl font-bold text-white mb-4">SchoolCRM</h2>
              <p className="text-white/70 text-lg">Professional CRM for Education</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
