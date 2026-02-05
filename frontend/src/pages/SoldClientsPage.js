import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { CheckCircle, Eye, RotateCcw, Filter, Calendar, User, Tag, Download, Loader2 } from 'lucide-react';

export default function SoldClientsPage() {
  const { t } = useLanguage();
  const { isAdmin } = useAuth();
  const { get, post, loading } = useApi();
  const navigate = useNavigate();

  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [tariffs, setTariffs] = useState([]);
  const [monthFilter, setMonthFilter] = useState('');
  const [managerFilter, setManagerFilter] = useState('');
  const [tariffFilter, setTariffFilter] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadSoldClients();
    loadTariffs();
    if (isAdmin) loadUsers();
  }, [monthFilter, managerFilter, tariffFilter, showArchived]);

  const loadSoldClients = async () => {
    try {
      const params = { 
        status: 'sold',
        is_archived: showArchived
      };
      if (managerFilter) params.manager_id = managerFilter;
      if (tariffFilter) params.tariff_id = tariffFilter;
      
      let data = await get('/api/clients', params);
      
      // Filter by month if selected
      if (monthFilter) {
        const [year, month] = monthFilter.split('-');
        data = data.filter(client => {
          const clientDate = new Date(client.created_at);
          return clientDate.getFullYear() === parseInt(year) && 
                 clientDate.getMonth() + 1 === parseInt(month);
        });
      }
      
      setClients(data);
    } catch (error) {
      console.error('Failed to load sold clients:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await get('/api/users');
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
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

  const handleArchive = async (client) => {
    try {
      await post(`/api/clients/${client.id}/archive`);
      toast.success(t.sold.clientArchived);
      loadSoldClients();
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleRestore = async (client) => {
    try {
      await post(`/api/clients/${client.id}/restore`);
      toast.success(t.sold.clientRestored);
      loadSoldClients();
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await fetch('/api/export/clients?format=csv&status=sold', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('crm_token')}`
        }
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sold_clients_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(t.clients.exportSuccess);
    } catch (error) {
      toast.error(t.common.error);
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (currency === 'UZS') {
      return `${amount?.toLocaleString() || 0} so'm`;
    }
    return `$${amount?.toLocaleString() || 0}`;
  };

  // Generate month options for the last 12 months
  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const label = date.toLocaleDateString('default', { year: 'numeric', month: 'long' });
      options.push({ value, label });
    }
    return options;
  };

  const totalRevenue = clients.reduce((sum, c) => sum + (c.tariff_price || 0), 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="sold-clients-page">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-text-primary flex items-center gap-3">
            <CheckCircle className="text-green-500" size={32} />
            {t.nav.soldClients}
          </h1>
          <p className="text-text-muted mt-1">{t.sold.description}</p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="btn-outline flex items-center gap-2 text-sm"
          data-testid="export-sold-button"
        >
          {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          {t.clients.exportClients}
        </button>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-text-muted text-sm">{t.sold.totalSold}</p>
          <p className="text-2xl font-bold text-text-primary">{clients.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-text-muted text-sm">{t.sold.totalRevenue}</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalRevenue, 'UZS')}</p>
        </div>
        <div className="card p-4">
          <p className="text-text-muted text-sm">{t.sold.activeDeals}</p>
          <p className="text-2xl font-bold text-text-primary">{clients.filter(c => !c.is_archived).length}</p>
        </div>
        <div className="card p-4">
          <p className="text-text-muted text-sm">{t.sold.archivedDeals}</p>
          <p className="text-2xl font-bold text-text-muted">{clients.filter(c => c.is_archived).length}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {/* Month Filter */}
        <div className="relative w-full sm:w-48">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <select
            value={monthFilter}
            onChange={(e) => setMonthFilter(e.target.value)}
            className="input-field pl-10 appearance-none"
            data-testid="month-filter"
          >
            <option value="">{t.sold.allMonths}</option>
            {getMonthOptions().map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Manager Filter (Admin Only) */}
        {isAdmin && (
          <div className="relative w-full sm:w-48">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
            <select
              value={managerFilter}
              onChange={(e) => setManagerFilter(e.target.value)}
              className="input-field pl-10 appearance-none"
              data-testid="manager-filter"
            >
              <option value="">{t.sold.allManagers}</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Tariff Filter */}
        <div className="relative w-full sm:w-48">
          <Tag className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={18} />
          <select
            value={tariffFilter}
            onChange={(e) => setTariffFilter(e.target.value)}
            className="input-field pl-10 appearance-none"
            data-testid="tariff-filter"
          >
            <option value="">{t.sold.allTariffs}</option>
            {tariffs.map((tariff) => (
              <option key={tariff.id} value={tariff.id}>{tariff.name}</option>
            ))}
          </select>
        </div>

        {/* Archive Toggle */}
        <button
          onClick={() => setShowArchived(!showArchived)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
            showArchived 
              ? 'bg-primary text-black border-primary' 
              : 'border-border hover:bg-gray-50'
          }`}
          data-testid="show-archived-toggle"
        >
          <Filter size={18} />
          <span>{showArchived ? t.sold.showingArchived : t.sold.showActive}</span>
        </button>
      </div>

      {/* Clients List */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]" data-testid="sold-clients-table">
            <thead>
              <tr className="table-header">
                <th className="text-left p-3 lg:p-4">{t.clients.name}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.phone}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.tariff}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.manager}</th>
                <th className="text-left p-3 lg:p-4">{t.sold.soldDate}</th>
                <th className="text-left p-3 lg:p-4">{t.common.actions}</th>
              </tr>
            </thead>
            <tbody>
              {clients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-text-muted">
                    {showArchived ? t.sold.noArchivedClients : t.sold.noSoldClients}
                  </td>
                </tr>
              ) : (
                clients.map((client) => (
                  <tr 
                    key={client.id} 
                    className={`table-row ${client.is_archived ? 'opacity-60' : ''}`}
                    data-testid={`sold-client-${client.id}`}
                  >
                    <td className="p-3 lg:p-4">
                      <div className="font-medium text-text-primary">{client.name}</div>
                      {client.is_archived && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                          {t.clients.archived}
                        </span>
                      )}
                      {client.group_name && (
                        <span 
                          className="text-xs px-2 py-0.5 rounded ml-1"
                          style={{ backgroundColor: `${client.group_color || '#6B7280'}20`, color: client.group_color || '#6B7280' }}
                        >
                          {client.group_name}
                        </span>
                      )}
                    </td>
                    <td className="p-3 lg:p-4 text-text-secondary">{client.phone}</td>
                    <td className="p-3 lg:p-4">
                      {client.tariff_name ? (
                        <div>
                          <div className="font-medium text-text-primary">{client.tariff_name}</div>
                          <div className="text-sm text-green-600">{formatCurrency(client.tariff_price, 'UZS')}</div>
                        </div>
                      ) : (
                        <span className="text-text-muted">-</span>
                      )}
                    </td>
                    <td className="p-3 lg:p-4 text-text-secondary">{client.manager_name || '-'}</td>
                    <td className="p-3 lg:p-4 text-text-muted">{formatDate(client.created_at)}</td>
                    <td className="p-3 lg:p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => navigate(`/clients/${client.id}`)}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          title={t.common.view}
                          data-testid={`view-sold-${client.id}`}
                        >
                          <Eye size={18} className="text-text-secondary" />
                        </button>
                        {client.is_archived ? (
                          <button
                            onClick={() => handleRestore(client)}
                            className="p-2 hover:bg-green-100 rounded-lg transition-colors"
                            title={t.sold.restore}
                            data-testid={`restore-client-${client.id}`}
                          >
                            <RotateCcw size={18} className="text-green-600" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleArchive(client)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title={t.sold.archive}
                            data-testid={`archive-client-${client.id}`}
                          >
                            <CheckCircle size={18} className="text-gray-500" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
