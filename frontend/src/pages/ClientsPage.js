import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { Plus, Search, Filter, Eye, Edit, Trash2, X, Loader2, Archive, Download, MessageSquare, Bell, Upload, FileSpreadsheet, CheckCircle, AlertCircle, Phone, CreditCard, Instagram, Copy, Check } from 'lucide-react';

export default function ClientsPage() {
  const { t } = useLanguage();
  const { isAdmin, isTelegram } = useAuth();
  const { get, post, put, del, loading } = useApi();
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  const phoneInputRef = useRef(null);

  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [tariffs, setTariffs] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [formData, setFormData] = useState({ 
    name: '', 
    phone: '', 
    source: 'Instagram', 
    status: 'new', 
    manager_id: '',
    tariff_id: '',
    group_id: '',
    initial_comment: '',
    reminder_text: '',
    reminder_at: ''
  });
  const [exporting, setExporting] = useState(false);
  const [showReminderFields, setShowReminderFields] = useState(false);
  
  // Quick Add Success State
  const [quickAddSuccess, setQuickAddSuccess] = useState(null); // Stores created client data
  
  // Import state
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [groups, setGroups] = useState([]);
  const [groupFilter, setGroupFilter] = useState('');

  const [clientsLoading, setClientsLoading] = useState(true);

  // Detect mobile
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  useEffect(() => {
    const loadAllData = async () => {
      setClientsLoading(true);
      await Promise.all([
        loadClients(),
        loadStatuses(),
        loadTariffs(),
        loadGroups(),
        isAdmin ? loadUsers() : Promise.resolve()
      ]);
      setClientsLoading(false);
    };
    loadAllData();
  }, [search, statusFilter, groupFilter, showArchived, location.key]);

  const loadClients = async () => {
    try {
      const params = { is_archived: showArchived, exclude_sold: true };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (groupFilter) params.group_id = groupFilter;
      
      // Direct axios call to avoid hook-related issues
      const token = localStorage.getItem('crm_token');
      const API_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${API_URL}/api/clients?${new URLSearchParams(params)}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await response.json();
      setClients(data || []);
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

  const loadGroups = async () => {
    try {
      const data = await get('/api/groups');
      setGroups(data);
    } catch (error) {
      console.error('Failed to load groups:', error);
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

  // Quick Add - minimal form for fast client creation (Instagram optimized)
  const handleQuickAdd = async (e) => {
    e.preventDefault();
    try {
      const createData = {
        name: formData.name,
        phone: formData.phone,
        source: formData.source || 'Instagram',
        status: 'new',
        manager_id: null,
        tariff_id: null,
        group_id: null,
        initial_comment: null,
        reminder_text: null,
        reminder_at: null
      };
      const response = await post('/api/clients', createData);
      
      // Haptic feedback in Telegram
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
      }
      
      // Show success state with action buttons
      setQuickAddSuccess({
        id: response.id,
        name: formData.name,
        phone: formData.phone
      });
      
      // Reset form for next entry
      setFormData({ 
        name: '', 
        phone: '', 
        source: 'Instagram', 
        status: 'new', 
        manager_id: '',
        tariff_id: '',
        group_id: '',
        initial_comment: '',
        reminder_text: '',
        reminder_at: ''
      });
      loadClients();
      
    } catch (error) {
      if (error?.response?.status === 400) {
        toast.error(t.clients.duplicatePhone);
      } else {
        toast.error(t.common.error);
      }
    }
  };

  // Close quick add and reset
  const closeQuickAdd = () => {
    setShowQuickAdd(false);
    setQuickAddSuccess(null);
    setFormData({ 
      name: '', 
      phone: '', 
      source: 'Instagram', 
      status: 'new', 
      manager_id: '',
      tariff_id: '',
      group_id: '',
      initial_comment: '',
      reminder_text: '',
      reminder_at: ''
    });
  };

  // Format phone for clean paste
  const handlePhonePaste = (e) => {
    e.preventDefault();
    const pastedText = e.clipboardData.getData('text');
    // Clean the phone number - keep only digits and +
    const cleanPhone = pastedText.replace(/[^\d+]/g, '');
    // Format if it looks like Uzbek number without +
    let formattedPhone = cleanPhone;
    if (cleanPhone.length === 9 && !cleanPhone.startsWith('+')) {
      formattedPhone = '+998' + cleanPhone;
    } else if (cleanPhone.length === 12 && cleanPhone.startsWith('998')) {
      formattedPhone = '+' + cleanPhone;
    }
    setFormData({ ...formData, phone: formattedPhone });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingClient) {
        const updateData = {
          name: formData.name,
          phone: formData.phone,
          source: formData.source,
          status: formData.status,
          manager_id: formData.manager_id,
          tariff_id: formData.tariff_id || null,
          group_id: formData.group_id || null
        };
        await put(`/api/clients/${editingClient.id}`, updateData);
        toast.success(t.clients.clientUpdated);
      } else {
        const createData = {
          name: formData.name,
          phone: formData.phone,
          source: formData.source,
          status: formData.status,
          manager_id: formData.manager_id || null,
          tariff_id: formData.tariff_id || null,
          group_id: formData.group_id || null,
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
        group_id: '',
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
      group_id: client.group_id || '',
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

  // Import handlers
  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      toast.error(t.import.selectFile);
      return;
    }
    
    setImportFile(file);
    setImportPreview(null);
    setImportResult(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setImporting(true);
      const response = await fetch('/api/import/preview', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('crm_token')}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Preview failed');
      }
      
      const preview = await response.json();
      setImportPreview(preview);
    } catch (error) {
      toast.error(error.message || t.import.importFailed);
      setImportFile(null);
    } finally {
      setImporting(false);
    }
  };

  const handleImportConfirm = async () => {
    if (!importPreview || importPreview.valid === 0) {
      toast.error(t.import.importFailed);
      return;
    }
    
    try {
      setImporting(true);
      
      const validRows = importPreview.rows.filter(r => r.valid).map(r => ({
        name: r.name,
        phone: r.phone,
        source: r.source || '',
        status: r.status || 'new',
        manager_id: null
      }));
      
      const response = await fetch('/api/import/save', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('crm_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(validRows)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Import failed');
      }
      
      const result = await response.json();
      setImportResult(result);
      
      if (result.success > 0) {
        toast.success(`${t.import.importSuccess}: ${result.success} ${t.clients.title.toLowerCase()}`);
        loadClients();
      }
    } catch (error) {
      toast.error(error.message || t.import.importFailed);
    } finally {
      setImporting(false);
    }
  };

  const resetImportModal = () => {
    setShowImportModal(false);
    setImportFile(null);
    setImportPreview(null);
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
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

  // Format phone for tel: link
  const formatPhoneLink = (phone) => {
    return phone.replace(/[^+\d]/g, '');
  };

  return (
    <div className="space-y-4 md:space-y-6 animate-fadeIn pb-20 md:pb-6" data-testid="clients-page">
      {/* Sticky Search Bar for Mobile */}
      <div className="sticky top-0 z-20 bg-white -mx-4 px-4 py-3 md:relative md:mx-0 md:px-0 md:py-0 md:bg-transparent border-b md:border-0 border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none z-10" size={20} />
          <input
            type="text"
            placeholder={t.clients.searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-11 pr-4 py-3 w-full text-base"
            data-testid="search-input"
          />
        </div>
      </div>

      {/* Header - Desktop */}
      <div className="hidden md:flex md:items-center md:justify-between gap-4">
        <h1 className="text-2xl lg:text-3xl font-bold text-text-primary">{t.clients.title}</h1>
        <div className="flex flex-wrap gap-2">
          {isAdmin && (
            <button
              onClick={() => setShowImportModal(true)}
              className="btn-outline flex items-center gap-2 text-sm"
              data-testid="import-button"
            >
              <Upload size={16} />
              {t.nav.import}
            </button>
          )}
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
                group_id: '',
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

      {/* Mobile Header */}
      <div className="flex md:hidden items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">{t.clients.title}</h1>
        <span className="text-sm text-text-muted">{clients.length} {t.clients.title.toLowerCase()}</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 md:gap-3">
        {/* Status Filter */}
        <div className="relative flex-1 min-w-[120px] md:flex-none">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field pl-3 pr-8 py-2.5 w-full md:w-40 appearance-none bg-white text-sm"
            data-testid="status-filter"
          >
            <option value="">{t.clients.allStatuses}</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.name}>{t.statuses[s.name] || s.name}</option>
            ))}
          </select>
          <svg className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" width="12" height="12" viewBox="0 0 12 12">
            <path d="M3 5l3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        
        {/* Group Filter */}
        {groups.length > 0 && (
          <div className="relative flex-1 min-w-[120px] md:flex-none">
            <select
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
              className="input-field pr-8 py-2.5 w-full md:w-40 appearance-none bg-white text-sm"
              data-testid="group-filter"
            >
              <option value="">{t.groups?.allGroups || 'All Groups'}</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>
            <svg className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" width="12" height="12" viewBox="0 0 12 12">
              <path d="M3 5l3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
        
        {/* Archive Toggle */}
        <button
          onClick={() => setShowArchived(!showArchived)}
          className={`flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg border transition-colors text-sm whitespace-nowrap ${
            showArchived ? 'bg-gray-100 border-gray-300 text-gray-700' : 'border-border hover:bg-gray-50 text-text-secondary'
          }`}
          data-testid="archive-toggle"
        >
          <Archive size={16} />
          <span className="hidden sm:inline">{t.clients.archived}</span>
        </button>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {clientsLoading ? (
          <div className="text-center py-12">
            <Loader2 className="animate-spin mx-auto h-8 w-8 text-primary" />
            <p className="text-text-muted mt-2">{t.common.loading || 'Loading...'}</p>
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-12 text-text-muted">
            {t.clients.noClients}
          </div>
        ) : (
          clients.map((client) => (
            <div 
              key={client.id} 
              className="card p-4 space-y-3 active:bg-gray-50 transition-colors"
              data-testid={`client-card-${client.id}`}
            >
              {/* Client Name & Status Row */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h3 
                    className="font-semibold text-text-primary text-base truncate cursor-pointer"
                    onClick={() => navigate(`/clients/${client.id}`)}
                  >
                    {client.name}
                  </h3>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    <span 
                      className="status-badge text-xs px-2 py-0.5"
                      style={{ backgroundColor: `${getStatusColor(client.status)}20`, color: getStatusColor(client.status) }}
                    >
                      {t.statuses[client.status] || client.status}
                    </span>
                    {client.group_name && (
                      <span 
                        className="text-xs px-2 py-0.5 rounded"
                        style={{ backgroundColor: `${client.group_color || '#6B7280'}20`, color: client.group_color || '#6B7280' }}
                      >
                        {client.group_name}
                      </span>
                    )}
                  </div>
                </div>
                <span className="text-xs text-text-muted whitespace-nowrap">
                  {formatDate(client.created_at)}
                </span>
              </div>

              {/* Phone Number - Clickable */}
              <a 
                href={`tel:${formatPhoneLink(client.phone)}`}
                className="flex items-center gap-2 text-primary font-medium text-base py-2 -my-1 active:opacity-70"
                data-testid={`call-client-${client.id}`}
              >
                <Phone size={18} />
                {client.phone}
              </a>

              {/* Quick Actions */}
              <div className="flex gap-2 pt-1 border-t border-border">
                {/* Call Button */}
                <a 
                  href={`tel:${formatPhoneLink(client.phone)}`}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-50 text-green-700 rounded-lg font-medium active:bg-green-100 transition-colors"
                  data-testid={`quick-call-${client.id}`}
                >
                  <Phone size={18} />
                  {t.clients?.call || 'Call'}
                </a>
                
                {/* Add Payment Button */}
                <button
                  onClick={() => navigate(`/clients/${client.id}?tab=payments&action=add`)}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-50 text-blue-700 rounded-lg font-medium active:bg-blue-100 transition-colors"
                  data-testid={`quick-payment-${client.id}`}
                >
                  <CreditCard size={18} />
                  {t.payments?.addPayment || 'Payment'}
                </button>
                
                {/* Edit Button */}
                <button
                  onClick={() => handleEdit(client)}
                  className="flex items-center justify-center p-3 bg-gray-50 text-text-secondary rounded-lg active:bg-gray-100 transition-colors"
                  data-testid={`quick-edit-${client.id}`}
                >
                  <Edit size={18} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block card overflow-hidden">
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
                      <div className="flex flex-wrap gap-1 mt-1">
                        {client.is_lead && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">{t.clients.isLead}</span>
                        )}
                        {client.group_name && (
                          <span 
                            className="text-xs px-2 py-0.5 rounded"
                            style={{ backgroundColor: `${client.group_color || '#6B7280'}20`, color: client.group_color || '#6B7280' }}
                            data-testid={`client-group-badge-${client.id}`}
                          >
                            {client.group_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-3 lg:p-4">
                      <a 
                        href={`tel:${formatPhoneLink(client.phone)}`}
                        className="text-primary hover:underline flex items-center gap-1.5"
                      >
                        <Phone size={14} />
                        {client.phone}
                      </a>
                    </td>
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

      {/* Floating Add Button - Mobile Only */}
      <button
        onClick={() => setShowQuickAdd(true)}
        className="md:hidden fixed bottom-6 right-6 w-14 h-14 bg-primary text-black rounded-full shadow-lg flex items-center justify-center z-30 active:scale-95 transition-transform"
        style={{ boxShadow: '0 4px 14px rgba(250, 204, 21, 0.4)' }}
        data-testid="floating-add-button"
      >
        <Plus size={28} strokeWidth={2.5} />
      </button>

      {/* Quick Add Modal - Instagram Optimized */}
      {showQuickAdd && (
        <div className="fixed inset-0 z-50 bg-black/50" onClick={closeQuickAdd}>
          <div 
            className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl animate-slideUp"
            onClick={(e) => e.stopPropagation()}
            data-testid="quick-add-modal"
          >
            <div className="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mt-3" />
            <div className="p-5">
              
              {/* Success State - Show after client created */}
              {quickAddSuccess ? (
                <div className="space-y-4" data-testid="quick-add-success">
                  {/* Success Header */}
                  <div className="text-center py-2">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                      <CheckCircle size={32} className="text-green-600" />
                    </div>
                    <h3 className="text-lg font-bold text-text-primary">{quickAddSuccess.name}</h3>
                    <p className="text-text-secondary">{quickAddSuccess.phone}</p>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="grid grid-cols-3 gap-3">
                    {/* Call */}
                    <a
                      href={`tel:${formatPhoneLink(quickAddSuccess.phone)}`}
                      className="flex flex-col items-center gap-2 p-4 bg-green-50 text-green-700 rounded-xl active:bg-green-100 transition-colors"
                      data-testid="success-call"
                    >
                      <Phone size={24} />
                      <span className="text-sm font-medium">{t.clients?.call || 'Call'}</span>
                    </a>
                    
                    {/* Add Reminder */}
                    <button
                      onClick={() => {
                        closeQuickAdd();
                        navigate(`/clients/${quickAddSuccess.id}?tab=reminders&action=add`);
                      }}
                      className="flex flex-col items-center gap-2 p-4 bg-yellow-50 text-yellow-700 rounded-xl active:bg-yellow-100 transition-colors"
                      data-testid="success-reminder"
                    >
                      <Bell size={24} />
                      <span className="text-sm font-medium">{t.clients?.reminder || 'Reminder'}</span>
                    </button>
                    
                    {/* Add Note */}
                    <button
                      onClick={() => {
                        closeQuickAdd();
                        navigate(`/clients/${quickAddSuccess.id}?tab=notes&action=add`);
                      }}
                      className="flex flex-col items-center gap-2 p-4 bg-blue-50 text-blue-700 rounded-xl active:bg-blue-100 transition-colors"
                      data-testid="success-note"
                    >
                      <MessageSquare size={24} />
                      <span className="text-sm font-medium">{t.clients?.note || 'Note'}</span>
                    </button>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => {
                        closeQuickAdd();
                        navigate(`/clients/${quickAddSuccess.id}`);
                      }}
                      className="btn-outline flex-1 py-3 flex items-center justify-center gap-2"
                      data-testid="success-view"
                    >
                      <Eye size={18} />
                      {t.clients?.viewClient || 'View'}
                    </button>
                    <button
                      onClick={() => setQuickAddSuccess(null)}
                      className="btn-primary flex-1 py-3 flex items-center justify-center gap-2"
                      data-testid="success-add-another"
                    >
                      <Plus size={18} />
                      {t.clients?.addAnother || 'Add Another'}
                    </button>
                  </div>
                </div>
              ) : (
                /* Form State - Quick Add Form */
                <>
                  <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
                    <Instagram size={20} className="text-pink-600" />
                    {t.clients?.quickAddInstagram || 'Add Instagram Lead'}
                  </h3>
                  <form onSubmit={handleQuickAdd} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1.5">{t.clients.name} *</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input-field py-3 text-base"
                        placeholder="Ism Familiya"
                        required
                        autoFocus
                        data-testid="quick-add-name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1.5">
                        {t.clients.phone} * 
                        <span className="text-text-muted font-normal ml-1">({t.clients?.pastePhone || 'paste from chat'})</span>
                      </label>
                      <input
                        ref={phoneInputRef}
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        onPaste={handlePhonePaste}
                        className="input-field py-3 text-base font-mono"
                        placeholder="+998 90 123 45 67"
                        required
                        data-testid="quick-add-phone"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-text-primary mb-1.5">
                        {t.clients.source}
                      </label>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, source: 'Instagram' })}
                          className={`flex-1 py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-1.5 transition-colors ${
                            formData.source === 'Instagram' 
                              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' 
                              : 'bg-gray-100 text-text-secondary'
                          }`}
                        >
                          <Instagram size={16} />
                          Instagram
                        </button>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, source: 'Telegram' })}
                          className={`flex-1 py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-1.5 transition-colors ${
                            formData.source === 'Telegram' 
                              ? 'bg-blue-500 text-white' 
                              : 'bg-gray-100 text-text-secondary'
                          }`}
                        >
                          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                          </svg>
                          Telegram
                        </button>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, source: '' })}
                          className={`px-3 py-2.5 rounded-lg font-medium text-sm transition-colors ${
                            !formData.source 
                              ? 'bg-gray-300 text-text-primary' 
                              : 'bg-gray-100 text-text-secondary'
                          }`}
                        >
                          {t.common?.other || 'Other'}
                        </button>
                      </div>
                    </div>
                    <div className="flex gap-3 pt-2">
                      <button
                        type="button"
                        onClick={closeQuickAdd}
                        className="btn-outline flex-1 py-3"
                      >
                        {t.common.cancel}
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary flex-1 py-3 flex items-center justify-center gap-2"
                        data-testid="quick-add-submit"
                      >
                        {loading && <Loader2 size={18} className="animate-spin" />}
                        {t.common.save}
                      </button>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        closeQuickAdd();
                        setShowModal(true);
                      }}
                      className="w-full text-center text-sm text-primary py-2"
                    >
                      {t.clients?.fullForm || 'Open full form →'}
                    </button>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full Add/Edit Modal */}
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
            <form onSubmit={handleSubmit} className="p-4 lg:p-6 space-y-4 max-h-[70vh] overflow-y-auto">
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
              
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.clients.tariff} <span className="text-text-muted font-normal">({t.common.optional})</span>
                </label>
                <select
                  value={formData.tariff_id}
                  onChange={(e) => setFormData({ ...formData, tariff_id: e.target.value })}
                  className="input-field"
                  data-testid="client-tariff-select"
                >
                  <option value="">{t.clients.selectTariff}</option>
                  {tariffs.map((tariff) => (
                    <option key={tariff.id} value={tariff.id}>
                      {tariff.name} - {tariff.price} {tariff.currency}
                    </option>
                  ))}
                </select>
              </div>

              {groups.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    {t.groups?.title || 'Group'} <span className="text-text-muted font-normal">({t.common.optional})</span>
                  </label>
                  <select
                    value={formData.group_id}
                    onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
                    className="input-field"
                    data-testid="client-group-select"
                  >
                    <option value="">{t.groups?.selectGroup || 'Select group'}</option>
                    {groups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {!editingClient && (
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    <MessageSquare size={16} className="inline mr-2" />
                    {t.clients.initialComment} <span className="text-text-muted font-normal">({t.common.optional})</span>
                  </label>
                  <textarea
                    value={formData.initial_comment}
                    onChange={(e) => setFormData({ ...formData, initial_comment: e.target.value })}
                    className="input-field min-h-[80px] resize-y"
                    placeholder={t.notes.placeholder}
                    data-testid="client-initial-comment"
                  />
                </div>
              )}

              {!editingClient && (
                <div className="space-y-3">
                  <button
                    type="button"
                    onClick={() => setShowReminderFields(!showReminderFields)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                      showReminderFields 
                        ? 'bg-primary/10 border-primary text-primary' 
                        : 'border-border hover:bg-gray-50 text-text-secondary'
                    }`}
                    data-testid="toggle-reminder-button"
                  >
                    <Bell size={16} />
                    {t.clients.setReminder}
                  </button>
                  
                  {showReminderFields && (
                    <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-border animate-fadeIn">
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          {t.reminders.reminderText}
                        </label>
                        <input
                          type="text"
                          value={formData.reminder_text}
                          onChange={(e) => setFormData({ ...formData, reminder_text: e.target.value })}
                          className="input-field"
                          placeholder={t.reminders.reminderText}
                          data-testid="client-reminder-text"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-text-primary mb-2">
                          {t.reminders.remindAt}
                        </label>
                        <input
                          type="datetime-local"
                          value={formData.reminder_at}
                          onChange={(e) => setFormData({ ...formData, reminder_at: e.target.value })}
                          className="input-field"
                          data-testid="client-reminder-at"
                        />
                      </div>
                    </div>
                  )}
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

      {/* Import Modal - Keep as is for desktop */}
      {showImportModal && (
        <div className="modal-overlay" onClick={resetImportModal}>
          <div className="modal-content max-w-2xl" onClick={(e) => e.stopPropagation()} data-testid="import-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                <FileSpreadsheet size={20} />
                {t.import.title}
              </h2>
              <button
                onClick={resetImportModal}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                data-testid="close-import-modal"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-4 lg:p-6 space-y-6">
              {!importResult && (
                <div className="space-y-4">
                  <div 
                    className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="import-drop-zone"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileSelect}
                      className="hidden"
                      data-testid="import-file-input"
                    />
                    <Upload size={48} className="mx-auto mb-4 text-text-muted" />
                    <p className="text-text-primary font-medium mb-2">{t.import.uploadFile}</p>
                    <p className="text-text-muted text-sm">{t.import.selectFile}</p>
                    {importFile && (
                      <p className="mt-4 text-sm text-primary font-medium">
                        {importFile.name}
                      </p>
                    )}
                  </div>
                  
                  {importing && (
                    <div className="flex items-center justify-center gap-2 py-4">
                      <Loader2 size={24} className="animate-spin text-primary" />
                      <span className="text-text-secondary">{t.import.importing}</span>
                    </div>
                  )}
                </div>
              )}

              {importPreview && !importResult && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-background-subtle p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-text-primary">{importPreview.total}</p>
                      <p className="text-sm text-text-muted">{t.import.totalRows}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-green-600">{importPreview.valid}</p>
                      <p className="text-sm text-text-muted">{t.import.validRows}</p>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-yellow-600">{importPreview.duplicates}</p>
                      <p className="text-sm text-text-muted">{t.import.duplicates}</p>
                    </div>
                    <div className="bg-red-50 p-4 rounded-lg text-center">
                      <p className="text-2xl font-bold text-red-600">{importPreview.errors}</p>
                      <p className="text-sm text-text-muted">{t.import.errors}</p>
                    </div>
                  </div>
                  
                  <div className="border border-border rounded-lg overflow-hidden">
                    <div className="overflow-x-auto max-h-64">
                      <table className="w-full text-sm">
                        <thead className="bg-background-subtle sticky top-0">
                          <tr>
                            <th className="text-left p-3 font-medium">#</th>
                            <th className="text-left p-3 font-medium">{t.clients.name}</th>
                            <th className="text-left p-3 font-medium">{t.clients.phone}</th>
                            <th className="text-left p-3 font-medium">{t.clients.source}</th>
                            <th className="text-left p-3 font-medium">{t.clients.status}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {importPreview.rows.slice(0, 20).map((row, idx) => (
                            <tr 
                              key={idx} 
                              className={`border-t border-border ${row.is_duplicate ? 'bg-yellow-50' : row.valid ? '' : 'bg-red-50'}`}
                            >
                              <td className="p-3">
                                {row.valid ? (
                                  <CheckCircle size={16} className="text-green-500" />
                                ) : (
                                  <AlertCircle size={16} className={row.is_duplicate ? "text-yellow-500" : "text-red-500"} />
                                )}
                              </td>
                              <td className="p-3">{row.name}</td>
                              <td className="p-3">{row.phone}</td>
                              <td className="p-3">{row.source || '-'}</td>
                              <td className="p-3">{row.status}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {importPreview.rows.length > 20 && (
                      <p className="text-center text-sm text-text-muted py-2 border-t border-border">
                        ... {importPreview.rows.length - 20} more rows
                      </p>
                    )}
                  </div>
                  
                  <div className="flex gap-3">
                    <button 
                      onClick={resetImportModal}
                      className="btn-outline flex-1"
                    >
                      {t.common.cancel}
                    </button>
                    <button 
                      onClick={handleImportConfirm}
                      disabled={importing || importPreview.valid === 0}
                      className="btn-primary flex-1 flex items-center justify-center gap-2"
                      data-testid="confirm-import-button"
                    >
                      {importing && <Loader2 size={18} className="animate-spin" />}
                      {t.import.confirmImport} ({importPreview.valid})
                    </button>
                  </div>
                </div>
              )}

              {importResult && (
                <div className="space-y-4">
                  <div className="text-center py-6">
                    {importResult.success > 0 ? (
                      <CheckCircle size={64} className="mx-auto mb-4 text-green-500" />
                    ) : (
                      <AlertCircle size={64} className="mx-auto mb-4 text-red-500" />
                    )}
                    <h3 className="text-xl font-bold text-text-primary mb-2">
                      {importResult.success > 0 ? t.import.importSuccess : t.import.importFailed}
                    </h3>
                    <p className="text-text-secondary">
                      {importResult.success} {t.import.validRows.toLowerCase()} • {importResult.failed} {t.import.errors.toLowerCase()}
                    </p>
                  </div>
                  
                  {importResult.failed_rows && importResult.failed_rows.length > 0 && (
                    <div className="bg-red-50 p-4 rounded-lg">
                      <h4 className="font-medium text-red-800 mb-2">{t.import.errors}:</h4>
                      <ul className="text-sm text-red-700 space-y-1">
                        {importResult.failed_rows.slice(0, 5).map((row, idx) => (
                          <li key={idx}>Row {row.row}: {row.phone} - {row.error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <button 
                    onClick={resetImportModal}
                    className="btn-primary w-full"
                    data-testid="close-import-result"
                  >
                    {t.common.close}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CSS for slide up animation */}
      <style>{`
        @keyframes slideUp {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
