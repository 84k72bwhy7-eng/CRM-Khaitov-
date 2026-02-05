import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { User, Lock, Globe, Loader2, Palette, Plus, Edit, Trash2, X, DollarSign, Tag } from 'lucide-react';

export default function SettingsPage() {
  const { t, language, switchLanguage } = useLanguage();
  const { user, updateUser, isAdmin } = useAuth();
  const { get, post, put, del, loading } = useApi();

  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || ''
  });
  const [passwordForm, setPasswordForm] = useState({ password: '' });
  const [statuses, setStatuses] = useState([]);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [editingStatus, setEditingStatus] = useState(null);
  const [statusForm, setStatusForm] = useState({ name: '', color: '#3B82F6', order: 0 });
  
  // Tariff Management State
  const [tariffs, setTariffs] = useState([]);
  const [showTariffModal, setShowTariffModal] = useState(false);
  const [editingTariff, setEditingTariff] = useState(null);
  const [tariffForm, setTariffForm] = useState({ name: '', price: 0, currency: 'USD', description: '' });
  
  // Currency Settings State
  const [systemSettings, setSystemSettings] = useState({ currency: 'USD' });
  const [savingCurrency, setSavingCurrency] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadStatuses();
      loadTariffs();
      loadSettings();
    }
  }, [isAdmin]);

  const loadStatuses = async () => {
    try {
      const data = await get('/api/statuses');
      setStatuses(data);
    } catch (error) {
      console.error('Failed to load statuses:', error);
    }
  };

  const loadTariffs = async () => {
    try {
      const data = await get('/api/tariffs');
      setTariffs(data);
    } catch (error) {
      console.error('Failed to load tariffs:', error);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await get('/api/settings');
      if (data) {
        setSystemSettings({ currency: data.currency || 'USD' });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

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

  const handleStatusSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingStatus) {
        await put(`/api/statuses/${editingStatus.id}`, statusForm);
        toast.success(t.statuses.statusUpdated);
      } else {
        await post('/api/statuses', statusForm);
        toast.success(t.statuses.statusCreated);
      }
      setShowStatusModal(false);
      setEditingStatus(null);
      setStatusForm({ name: '', color: '#3B82F6', order: 0 });
      loadStatuses();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const handleEditStatus = (status) => {
    setEditingStatus(status);
    setStatusForm({
      name: status.name,
      color: status.color,
      order: status.order
    });
    setShowStatusModal(true);
  };

  const handleDeleteStatus = async (status) => {
    if (status.is_default) {
      toast.error(t.statuses.cannotDeleteDefault);
      return;
    }
    try {
      await del(`/api/statuses/${status.id}`);
      toast.success(t.statuses.statusDeleted);
      loadStatuses();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const colorOptions = [
    '#3B82F6', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', 
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
  ];

  return (
    <div className="space-y-8 animate-fadeIn" data-testid="settings-page">
      <h1 className="text-2xl lg:text-3xl font-bold text-text-primary">{t.settings.title}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <div className="card" data-testid="profile-settings">
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
              <User size={20} />
              {t.settings.profile}
            </h2>
          </div>
          <form onSubmit={handleUpdateProfile} className="p-4 lg:p-6 space-y-4">
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
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
              <Lock size={20} />
              {t.settings.changePassword}
            </h2>
          </div>
          <form onSubmit={handleChangePassword} className="p-4 lg:p-6 space-y-4">
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
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
              <Globe size={20} />
              {t.settings.language}
            </h2>
          </div>
          <div className="p-4 lg:p-6">
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

        {/* Status Management (Admin Only) */}
        {isAdmin && (
          <div className="card" data-testid="status-settings">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <Palette size={20} />
                {t.settings.statusManagement}
              </h2>
              <button
                onClick={() => {
                  setEditingStatus(null);
                  setStatusForm({ name: '', color: '#3B82F6', order: statuses.length });
                  setShowStatusModal(true);
                }}
                className="btn-primary flex items-center gap-2 text-sm"
                data-testid="add-status-button"
              >
                <Plus size={16} />
                {t.statuses.addStatus}
              </button>
            </div>
            <div className="p-4 lg:p-6">
              {statuses.length === 0 ? (
                <p className="text-text-muted text-center py-4">{t.common.loading}</p>
              ) : (
                <div className="space-y-3">
                  {statuses.map((status) => (
                    <div
                      key={status.id}
                      className="flex items-center justify-between p-3 bg-background-subtle rounded-lg"
                      data-testid={`status-item-${status.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-6 h-6 rounded-full"
                          style={{ backgroundColor: status.color }}
                        />
                        <div>
                          <p className="font-medium text-text-primary">
                            {t.statuses[status.name] || status.name}
                            {status.is_default && (
                              <span className="ml-2 text-xs text-text-muted">(default)</span>
                            )}
                          </p>
                          <p className="text-sm text-text-muted">Order: {status.order}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEditStatus(status)}
                          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                        >
                          <Edit size={16} className="text-text-secondary" />
                        </button>
                        {!status.is_default && (
                          <button
                            onClick={() => handleDeleteStatus(status)}
                            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                          >
                            <Trash2 size={16} className="text-status-error" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Status Modal */}
      {showStatusModal && (
        <div className="modal-overlay" onClick={() => setShowStatusModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="status-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">
                {editingStatus ? t.statuses.editStatus : t.statuses.addStatus}
              </h2>
              <button onClick={() => setShowStatusModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleStatusSubmit} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.statuses.statusName}</label>
                <input
                  type="text"
                  value={statusForm.name}
                  onChange={(e) => setStatusForm({ ...statusForm, name: e.target.value })}
                  className="input-field"
                  required
                  data-testid="status-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.statuses.statusColor}</label>
                <div className="flex flex-wrap gap-2">
                  {colorOptions.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setStatusForm({ ...statusForm, color })}
                      className={`w-8 h-8 rounded-full transition-transform ${
                        statusForm.color === color ? 'ring-2 ring-offset-2 ring-black scale-110' : ''
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.statuses.statusOrder}</label>
                <input
                  type="number"
                  value={statusForm.order}
                  onChange={(e) => setStatusForm({ ...statusForm, order: parseInt(e.target.value) })}
                  className="input-field"
                  min="0"
                  data-testid="status-order-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowStatusModal(false)} className="btn-outline flex-1">
                  {t.common.cancel}
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
                  {loading && <Loader2 size={18} className="animate-spin" />}
                  {t.common.save}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
