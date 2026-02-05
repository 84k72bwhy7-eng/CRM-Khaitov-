import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { Plus, Search, Filter, Eye, Edit, Trash2, X, Loader2, Archive, Download, MessageSquare, Bell } from 'lucide-react';

export default function ClientsPage() {
  const { t } = useLanguage();
  const { isAdmin } = useAuth();
  const { get, post, put, del, loading } = useApi();
  const navigate = useNavigate();

  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [tariffs, setTariffs] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [formData, setFormData] = useState({ 
    name: '', 
    phone: '', 
    source: '', 
    status: 'new', 
    manager_id: '',
    tariff_id: '',
    initial_comment: '',
    reminder_text: '',
    reminder_at: ''
  });
  const [exporting, setExporting] = useState(false);
  const [showReminderFields, setShowReminderFields] = useState(false);

  useEffect(() => {
    loadClients();
    loadStatuses();
    loadTariffs();
    if (isAdmin) loadUsers();
  }, [search, statusFilter, showArchived]);

  const loadClients = async () => {
    try {
      const params = { is_archived: showArchived };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const data = await get('/api/clients', params);
      setClients(data);
    } catch (error) {
      console.error('Failed to load clients:', error);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingClient) {
        // For editing, only send basic fields (no comment/reminder)
        const updateData = {
          name: formData.name,
          phone: formData.phone,
          source: formData.source,
          status: formData.status,
          manager_id: formData.manager_id,
          tariff_id: formData.tariff_id || null
        };
        await put(`/api/clients/${editingClient.id}`, updateData);
        toast.success(t.clients.clientUpdated);
      } else {
        // For creating, include comment and reminder
        const createData = {
          name: formData.name,
          phone: formData.phone,
          source: formData.source,
          status: formData.status,
          manager_id: formData.manager_id || null,
          tariff_id: formData.tariff_id || null,
          initial_comment: formData.initial_comment || null,
          reminder_text: showReminderFields && formData.reminder_text ? formData.reminder_text : null,
          reminder_at: showReminderFields && formData.reminder_at ? formData.reminder_at : null
        };
        await post('/api/clients', createData);
        toast.success(t.clients.clientCreated);
      }
      setShowModal(false);
      setEditingClient(null);
      setFormData({ 
        name: '', 
        phone: '', 
        source: '', 
        status: 'new', 
        manager_id: '',
        tariff_id: '',
        initial_comment: '',
        reminder_text: '',
        reminder_at: ''
      });
      setShowReminderFields(false);
      loadClients();
    } catch (error) {
      if (error?.response?.status === 400) {
        toast.error(t.clients.duplicatePhone);
      } else {
        toast.error(t.common.error);
      }
    }
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      phone: client.phone,
      source: client.source || '',
      status: client.status,
      manager_id: client.manager_id || '',
      tariff_id: client.tariff_id || '',
      initial_comment: '',
      reminder_text: '',
      reminder_at: ''
    });
    setShowReminderFields(false);
    setShowModal(true);
  };

  const handleDelete = async (client) => {
    if (window.confirm(t.clients.confirmDelete)) {
      try {
        await del(`/api/clients/${client.id}`);
        toast.success(t.clients.clientDeleted);
        loadClients();
      } catch (error) {
        toast.error(t.common.error);
      }
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await fetch('/api/export/clients?format=csv', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('crm_token')}`
        }
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'clients_export.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(t.common.success);
    } catch (error) {
      toast.error(t.common.error);
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const getStatusColor = (statusName) => {
    const status = statuses.find(s => s.name === statusName);
    return status?.color || '#3B82F6';
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="clients-page">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <h1 className="text-2xl lg:text-3xl font-bold text-text-primary">{t.clients.title}</h1>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="btn-outline flex items-center gap-2 text-sm"
            data-testid="export-button"
          >
            {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {t.clients.exportClients}
          </button>
          <button
            onClick={() => {
              setEditingClient(null);
              setFormData({ 
                name: '', 
                phone: '', 
                source: '', 
                status: 'new', 
                manager_id: '',
                tariff_id: '',
                initial_comment: '',
                reminder_text: '',
                reminder_at: ''
              });
              setShowReminderFields(false);
              setShowModal(true);
            }}
            className="btn-primary flex items-center gap-2 text-sm"
            data-testid="add-client-button"
          >
            <Plus size={18} />
            {t.clients.addClient}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
          <input
            type="text"
            placeholder={t.clients.searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-10"
            data-testid="search-input"
          />
        </div>
        <div className="relative w-full sm:w-48">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field pl-10 appearance-none"
            data-testid="status-filter"
          >
            <option value="">{t.clients.allStatuses}</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.name}>{t.statuses[s.name] || s.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => setShowArchived(!showArchived)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
            showArchived ? 'bg-gray-100 border-gray-300' : 'border-border hover:bg-gray-50'
          }`}
          data-testid="archive-toggle"
        >
          <Archive size={18} />
          <span className="hidden sm:inline">{t.clients.archived}</span>
        </button>
      </div>

      {/* Clients Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]" data-testid="clients-table">
            <thead>
              <tr className="table-header">
                <th className="text-left p-3 lg:p-4">{t.clients.name}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.phone}</th>
                <th className="text-left p-3 lg:p-4 hidden sm:table-cell">{t.clients.source}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.status}</th>
                <th className="text-left p-3 lg:p-4 hidden md:table-cell">{t.clients.createdAt}</th>
                <th className="text-left p-3 lg:p-4">{t.clients.actions}</th>
              </tr>
            </thead>
            <tbody>
              {clients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-text-muted">
                    {t.clients.noClients}
                  </td>
                </tr>
              ) : (
                clients.map((client) => (
                  <tr key={client.id} className="table-row" data-testid={`client-row-${client.id}`}>
                    <td className="p-3 lg:p-4">
                      <div className="font-medium text-text-primary">{client.name}</div>
                      {client.is_lead && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">{t.clients.isLead}</span>
                      )}
                    </td>
                    <td className="p-3 lg:p-4 text-text-secondary">{client.phone}</td>
                    <td className="p-3 lg:p-4 text-text-secondary hidden sm:table-cell">{client.source || '-'}</td>
                    <td className="p-3 lg:p-4">
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: `${getStatusColor(client.status)}20`, color: getStatusColor(client.status) }}
                      >
                        {t.statuses[client.status] || client.status}
                      </span>
                    </td>
                    <td className="p-3 lg:p-4 text-text-muted text-sm hidden md:table-cell">{formatDate(client.created_at)}</td>
                    <td className="p-3 lg:p-4">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => navigate(`/clients/${client.id}`)}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          data-testid={`view-client-${client.id}`}
                        >
                          <Eye size={16} className="text-text-secondary" />
                        </button>
                        <button
                          onClick={() => handleEdit(client)}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          data-testid={`edit-client-${client.id}`}
                        >
                          <Edit size={16} className="text-text-secondary" />
                        </button>
                        <button
                          onClick={() => handleDelete(client)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                          data-testid={`delete-client-${client.id}`}
                        >
                          <Trash2 size={16} className="text-status-error" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="client-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">
                {editingClient ? t.clients.editClient : t.clients.addClient}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                data-testid="close-modal-button"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.name}</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  required
                  data-testid="client-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.phone}</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input-field"
                  required
                  data-testid="client-phone-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.source}</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="input-field"
                  placeholder="Instagram, Telegram, etc."
                  data-testid="client-source-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.status}</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="input-field"
                  data-testid="client-status-select"
                >
                  {statuses.map((s) => (
                    <option key={s.id} value={s.name}>{t.statuses[s.name] || s.name}</option>
                  ))}
                </select>
              </div>
              {isAdmin && (
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.manager}</label>
                  <select
                    value={formData.manager_id}
                    onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                    className="input-field"
                    data-testid="client-manager-select"
                  >
                    <option value="">-</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>{user.name}</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-outline flex-1"
                  data-testid="cancel-button"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                  data-testid="save-client-button"
                >
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
