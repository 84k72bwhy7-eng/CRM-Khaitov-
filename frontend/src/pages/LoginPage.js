import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { toast } from 'sonner';
import { Eye, EyeOff, Globe, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t, language, switchLanguage } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success(t.auth.welcome);
      navigate('/');
    } catch (error) {
      toast.error(t.auth.loginError);
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
            <span className="text-primary">Course</span>CRM
          </h1>
          <p className="text-text-secondary mb-10">{t.auth.welcome}</p>

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
              {t.auth.loginButton}
            </button>
          </form>
        </div>
      </div>

      {/* Right side - Image */}
      <div
        className="hidden lg:block lg:w-1/2 bg-secondary relative overflow-hidden"
        data-testid="login-hero"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-secondary via-secondary to-primary/20" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-12">
            <div className="w-32 h-32 bg-primary rounded-2xl mx-auto mb-8 flex items-center justify-center">
              <span className="text-6xl font-bold text-black">C</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">CourseCRM</h2>
            <p className="text-white/70 text-lg">Professional CRM for Course Managers</p>
          </div>
        </div>
      </div>
    </div>
  );
}
