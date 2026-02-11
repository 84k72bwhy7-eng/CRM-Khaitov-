import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { User, Lock, Globe, Loader2, Palette, Plus, Edit, Trash2, X, DollarSign, Tag, Users } from 'lucide-react';

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
  
  // Group Management State
  const [groups, setGroups] = useState([]);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [groupForm, setGroupForm] = useState({ name: '', color: '#6B7280', description: '' });
  
  // Currency Settings State
  const [systemSettings, setSystemSettings] = useState({ currency: 'USD', exchange_rates: { USD: 12500 } });
  const [savingCurrency, setSavingCurrency] = useState(false);
  const [exchangeRateInput, setExchangeRateInput] = useState('12500');
  const [savingRate, setSavingRate] = useState(false);

  // Telegram Notification Status
  const [telegramStatus, setTelegramStatus] = useState(null);
  const [sendingTestNotification, setSendingTestNotification] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadStatuses();
      loadTariffs();
      loadGroups();
      loadSettings();
      loadTelegramStatus();
    }
  }, [isAdmin]);

  const loadTelegramStatus = async () => {
    try {
      const data = await get('/api/notifications/telegram-status');
      setTelegramStatus(data);
    } catch (error) {
      console.error('Failed to load Telegram status:', error);
    }
  };

  const sendTestNotification = async () => {
    setSendingTestNotification(true);
    try {
      await post('/api/notifications/test-telegram');
      toast.success(t.settings?.testNotificationSent || 'Test notification sent!');
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    } finally {
      setSendingTestNotification(false);
    }
  };

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
        setSystemSettings({ 
          currency: data.currency || 'USD',
          exchange_rates: data.exchange_rates || { USD: 12500 }
        });
        setExchangeRateInput(String(data.exchange_rates?.USD || 12500));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const loadGroups = async () => {
    try {
      const data = await get('/api/groups');
      setGroups(data);
    } catch (error) {
      console.error('Failed to load groups:', error);
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

  // Tariff handlers
  const handleTariffSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTariff) {
        await put(`/api/tariffs/${editingTariff.id}`, tariffForm);
        toast.success(t.tariffs.tariffUpdated);
      } else {
        await post('/api/tariffs', tariffForm);
        toast.success(t.tariffs.tariffCreated);
      }
      setShowTariffModal(false);
      setEditingTariff(null);
      setTariffForm({ name: '', price: 0, currency: 'USD', description: '' });
      loadTariffs();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const handleEditTariff = (tariff) => {
    setEditingTariff(tariff);
    setTariffForm({
      name: tariff.name,
      price: tariff.price,
      currency: tariff.currency || 'USD',
      description: tariff.description || ''
    });
    setShowTariffModal(true);
  };

  const handleDeleteTariff = async (tariff) => {
    try {
      await del(`/api/tariffs/${tariff.id}`);
      toast.success(t.tariffs.tariffDeleted);
      loadTariffs();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.tariffs.tariffInUse);
    }
  };

  // Currency handler
  const handleCurrencyChange = async (currency) => {
    setSavingCurrency(true);
    try {
      await put('/api/settings', { currency });
      setSystemSettings({ ...systemSettings, currency });
      toast.success(t.settings.currencyUpdated);
    } catch (error) {
      toast.error(t.common.error);
    } finally {
      setSavingCurrency(false);
    }
  };

  // Exchange rate handler
  const handleExchangeRateUpdate = async () => {
    const rate = parseFloat(exchangeRateInput);
    if (isNaN(rate) || rate <= 0) {
      toast.error(t.settings?.invalidRate || 'Noto\'g\'ri kurs');
      return;
    }
    
    setSavingRate(true);
    try {
      await put('/api/settings/exchange-rate', {
        currency_code: 'USD',
        rate_to_uzs: rate
      });
      setSystemSettings({
        ...systemSettings,
        exchange_rates: { ...systemSettings.exchange_rates, USD: rate }
      });
      toast.success(t.settings?.rateUpdated || 'Valyuta kursi yangilandi');
      // Reload tariffs to get updated UZS prices
      loadTariffs();
    } catch (error) {
      toast.error(t.common.error);
    } finally {
      setSavingRate(false);
    }
  };

  // Group handlers
  const handleGroupSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingGroup) {
        await put(`/api/groups/${editingGroup.id}`, groupForm);
        toast.success(t.groups.groupUpdated);
      } else {
        await post('/api/groups', groupForm);
        toast.success(t.groups.groupCreated);
      }
      setShowGroupModal(false);
      setEditingGroup(null);
      setGroupForm({ name: '', color: '#6B7280', description: '' });
      loadGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const handleEditGroup = (group) => {
    setEditingGroup(group);
    setGroupForm({
      name: group.name,
      color: group.color || '#6B7280',
      description: group.description || ''
    });
    setShowGroupModal(true);
  };

  const handleDeleteGroup = async (group) => {
    try {
      await del(`/api/groups/${group.id}`);
      toast.success(t.groups.groupDeleted);
      loadGroups();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.groups.groupInUse);
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

        {/* Tariff Management (Admin Only) */}
        {isAdmin && (
          <div className="card" data-testid="tariff-settings">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <Tag size={20} />
                {t.settings.tariffManagement}
              </h2>
              <button
                onClick={() => {
                  setEditingTariff(null);
                  setTariffForm({ name: '', price: 0, currency: systemSettings.currency, description: '' });
                  setShowTariffModal(true);
                }}
                className="btn-primary flex items-center gap-2 text-sm"
                data-testid="add-tariff-button"
              >
                <Plus size={16} />
                {t.tariffs.addTariff}
              </button>
            </div>
            <div className="p-4 lg:p-6">
              {tariffs.length === 0 ? (
                <p className="text-text-muted text-center py-4">{t.tariffs.noTariffs}</p>
              ) : (
                <div className="space-y-3">
                  {tariffs.map((tariff) => (
                    <div
                      key={tariff.id}
                      className="flex items-center justify-between p-3 bg-background-subtle rounded-lg"
                      data-testid={`tariff-item-${tariff.id}`}
                    >
                      <div>
                        <p className="font-medium text-text-primary">{tariff.name}</p>
                        <p className="text-sm text-text-muted">
                          {tariff.price.toLocaleString()} {tariff.currency}
                          {tariff.description && ` • ${tariff.description}`}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEditTariff(tariff)}
                          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                          data-testid={`edit-tariff-${tariff.id}`}
                        >
                          <Edit size={16} className="text-text-secondary" />
                        </button>
                        <button
                          onClick={() => handleDeleteTariff(tariff)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                          data-testid={`delete-tariff-${tariff.id}`}
                        >
                          <Trash2 size={16} className="text-status-error" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Currency Settings (Admin Only) */}
        {isAdmin && (
          <div className="card" data-testid="currency-settings">
            <div className="p-4 lg:p-6 border-b border-border">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <DollarSign size={20} />
                {t.settings.currencySettings}
              </h2>
            </div>
            <div className="p-4 lg:p-6 space-y-6">
              {/* Exchange Rate Input */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.settings?.exchangeRate || 'USD → UZS kursi'}
                </label>
                <div className="flex gap-3">
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">1 USD =</span>
                    <input
                      type="number"
                      value={exchangeRateInput}
                      onChange={(e) => setExchangeRateInput(e.target.value)}
                      className="input pl-20 pr-16 text-right font-semibold"
                      placeholder="12500"
                      min="1"
                      data-testid="exchange-rate-input"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">UZS</span>
                  </div>
                  <button
                    onClick={handleExchangeRateUpdate}
                    disabled={savingRate}
                    className="btn-primary px-6 flex items-center gap-2"
                    data-testid="save-exchange-rate"
                  >
                    {savingRate && <Loader2 size={16} className="animate-spin" />}
                    {t.common?.save || 'Saqlash'}
                  </button>
                </div>
                <p className="text-sm text-text-muted mt-2">
                  {t.settings?.exchangeRateHint || 'USD narxli tariflar avtomatik UZS ga o\'tkaziladi'}
                </p>
              </div>

              {/* Currency Selection */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">{t.settings.selectCurrency}</label>
                <div className="flex gap-4">
                  <button
                    onClick={() => handleCurrencyChange('USD')}
                    disabled={savingCurrency}
                    className={`flex-1 py-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                      systemSettings.currency === 'USD'
                        ? 'bg-primary text-black'
                        : 'bg-background-subtle text-text-secondary hover:bg-gray-100'
                    }`}
                    data-testid="currency-usd-button"
                  >
                    {savingCurrency && systemSettings.currency !== 'USD' && <Loader2 size={18} className="animate-spin" />}
                    $ USD
                  </button>
                  <button
                    onClick={() => handleCurrencyChange('UZS')}
                    disabled={savingCurrency}
                    className={`flex-1 py-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                      systemSettings.currency === 'UZS'
                        ? 'bg-primary text-black'
                        : 'bg-background-subtle text-text-secondary hover:bg-gray-100'
                    }`}
                    data-testid="currency-uzs-button"
                  >
                    {savingCurrency && systemSettings.currency !== 'UZS' && <Loader2 size={18} className="animate-spin" />}
                    UZS
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Telegram Notifications (Admin Only) */}
        {isAdmin && telegramStatus && (
          <div className="card" data-testid="telegram-settings">
            <div className="p-4 lg:p-6 border-b border-border">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                </svg>
                {t.settings?.telegramNotifications || 'Telegram Notifications'}
              </h2>
            </div>
            <div className="p-4 lg:p-6 space-y-4">
              {/* Status Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="bg-background-subtle p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-text-primary">{telegramStatus.users_with_telegram}/{telegramStatus.total_users}</p>
                  <p className="text-sm text-text-muted">{t.settings?.usersWithTelegram || 'Users linked'}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">{telegramStatus.telegram_sent}</p>
                  <p className="text-sm text-text-muted">{t.settings?.notificationsSent || 'Sent'}</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-yellow-600">{telegramStatus.pending_reminders}</p>
                  <p className="text-sm text-text-muted">{t.settings?.pendingReminders || 'Pending'}</p>
                </div>
                <div className={`p-4 rounded-lg text-center ${telegramStatus.scheduler_running ? 'bg-green-50' : 'bg-red-50'}`}>
                  <p className={`text-lg font-bold ${telegramStatus.scheduler_running ? 'text-green-600' : 'text-red-600'}`}>
                    {telegramStatus.scheduler_running ? '✓ Active' : '✗ Stopped'}
                  </p>
                  <p className="text-sm text-text-muted">{t.settings?.schedulerStatus || 'Scheduler'}</p>
                </div>
              </div>
              
              {/* Test Button */}
              {user?.telegram_id && (
                <button
                  onClick={sendTestNotification}
                  disabled={sendingTestNotification}
                  className="btn-outline w-full flex items-center justify-center gap-2"
                  data-testid="test-telegram-button"
                >
                  {sendingTestNotification ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                    </svg>
                  )}
                  {t.settings?.sendTestNotification || 'Send Test Notification'}
                </button>
              )}
              
              {!user?.telegram_id && (
                <p className="text-sm text-text-muted text-center py-2">
                  {t.settings?.linkTelegramFirst || 'Link your Telegram account to test notifications'}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Group Management (Admin Only) */}
        {isAdmin && (
          <div className="card" data-testid="group-settings">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <Users size={20} />
                {t.settings.groupManagement}
              </h2>
              <button
                onClick={() => {
                  setEditingGroup(null);
                  setGroupForm({ name: '', color: '#6B7280', description: '' });
                  setShowGroupModal(true);
                }}
                className="btn-primary flex items-center gap-2 text-sm"
                data-testid="add-group-button"
              >
                <Plus size={16} />
                {t.groups.addGroup}
              </button>
            </div>
            <div className="p-4 lg:p-6">
              {groups.length === 0 ? (
                <p className="text-text-muted text-center py-4">{t.groups.noGroups}</p>
              ) : (
                <div className="space-y-3">
                  {groups.map((group) => (
                    <div
                      key={group.id}
                      className="flex items-center justify-between p-3 bg-background-subtle rounded-lg"
                      data-testid={`group-item-${group.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: group.color || '#6B7280' }}
                        />
                        <div>
                          <p className="font-medium text-text-primary">{group.name}</p>
                          {group.description && (
                            <p className="text-sm text-text-muted">{group.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEditGroup(group)}
                          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                          data-testid={`edit-group-${group.id}`}
                        >
                          <Edit size={16} className="text-text-secondary" />
                        </button>
                        <button
                          onClick={() => handleDeleteGroup(group)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                          data-testid={`delete-group-${group.id}`}
                        >
                          <Trash2 size={16} className="text-status-error" />
                        </button>
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

      {/* Tariff Modal */}
      {showTariffModal && (
        <div className="modal-overlay" onClick={() => setShowTariffModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="tariff-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">
                {editingTariff ? t.tariffs.editTariff : t.tariffs.addTariff}
              </h2>
              <button onClick={() => setShowTariffModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleTariffSubmit} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.tariffs.tariffName}</label>
                <input
                  type="text"
                  value={tariffForm.name}
                  onChange={(e) => setTariffForm({ ...tariffForm, name: e.target.value })}
                  className="input-field"
                  required
                  data-testid="tariff-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">{t.tariffs.tariffPrice}</label>
                  <input
                    type="number"
                    value={tariffForm.price}
                    onChange={(e) => setTariffForm({ ...tariffForm, price: parseFloat(e.target.value) || 0 })}
                    className="input-field"
                    min="0"
                    step="0.01"
                    required
                    data-testid="tariff-price-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.currency}</label>
                  <select
                    value={tariffForm.currency}
                    onChange={(e) => setTariffForm({ ...tariffForm, currency: e.target.value })}
                    className="input-field"
                    data-testid="tariff-currency-select"
                  >
                    <option value="USD">USD</option>
                    <option value="UZS">UZS</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.tariffs.tariffDescription} <span className="text-text-muted font-normal">({t.common.optional})</span>
                </label>
                <textarea
                  value={tariffForm.description}
                  onChange={(e) => setTariffForm({ ...tariffForm, description: e.target.value })}
                  className="input-field min-h-[80px] resize-y"
                  data-testid="tariff-description-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowTariffModal(false)} className="btn-outline flex-1">
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

      {/* Group Modal */}
      {showGroupModal && (
        <div className="modal-overlay" onClick={() => setShowGroupModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="group-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">
                {editingGroup ? t.groups.editGroup : t.groups.addGroup}
              </h2>
              <button onClick={() => setShowGroupModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleGroupSubmit} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.groups.groupName}</label>
                <input
                  type="text"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                  className="input-field"
                  required
                  data-testid="group-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.groups.groupColor}</label>
                <div className="flex flex-wrap gap-2">
                  {colorOptions.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setGroupForm({ ...groupForm, color })}
                      className={`w-8 h-8 rounded-full transition-transform ${
                        groupForm.color === color ? 'ring-2 ring-offset-2 ring-black scale-110' : ''
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.groups.groupDescription} <span className="text-text-muted font-normal">({t.common.optional})</span>
                </label>
                <textarea
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({ ...groupForm, description: e.target.value })}
                  className="input-field min-h-[80px] resize-y"
                  data-testid="group-description-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowGroupModal(false)} className="btn-outline flex-1">
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
