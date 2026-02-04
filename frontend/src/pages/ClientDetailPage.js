import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { ArrowLeft, Edit, Trash2, Plus, Phone, User, Clock, FileText, CreditCard, Loader2, X } from 'lucide-react';

export default function ClientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { get, post, put, del, loading } = useApi();

  const [client, setClient] = useState(null);
  const [notes, setNotes] = useState([]);
  const [payments, setPayments] = useState([]);
  const [activeTab, setActiveTab] = useState('notes');
  const [newNote, setNewNote] = useState('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ amount: '', status: 'pending', date: '' });
  const [editingClient, setEditingClient] = useState(false);
  const [clientForm, setClientForm] = useState({ name: '', phone: '', source: '', status: '' });

  useEffect(() => {
    loadClientData();
  }, [id]);

  const loadClientData = async () => {
    try {
      const [clientData, notesData, paymentsData] = await Promise.all([
        get(`/api/clients/${id}`),
        get(`/api/notes/${id}`),
        get(`/api/payments/client/${id}`)
      ]);
      setClient(clientData);
      setClientForm({
        name: clientData.name,
        phone: clientData.phone,
        source: clientData.source || '',
        status: clientData.status
      });
      setNotes(notesData);
      setPayments(paymentsData);
    } catch (error) {
      toast.error(t.common.error);
      navigate('/clients');
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await post('/api/notes', { client_id: id, text: newNote });
      toast.success(t.notes.noteAdded);
      setNewNote('');
      const notesData = await get(`/api/notes/${id}`);
      setNotes(notesData);
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleDeleteNote = async (noteId) => {
    try {
      await del(`/api/notes/${noteId}`);
      toast.success(t.notes.noteDeleted);
      setNotes(notes.filter(n => n.id !== noteId));
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleAddPayment = async (e) => {
    e.preventDefault();
    try {
      await post('/api/payments', {
        client_id: id,
        amount: parseFloat(paymentForm.amount),
        status: paymentForm.status,
        date: paymentForm.date || undefined
      });
      toast.success(t.payments.paymentAdded);
      setShowPaymentModal(false);
      setPaymentForm({ amount: '', status: 'pending', date: '' });
      const paymentsData = await get(`/api/payments/client/${id}`);
      setPayments(paymentsData);
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleUpdateClient = async (e) => {
    e.preventDefault();
    try {
      const updated = await put(`/api/clients/${id}`, clientForm);
      setClient(updated);
      setEditingClient(false);
      toast.success(t.clients.clientUpdated);
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleDeleteClient = async () => {
    if (window.confirm(t.clients.confirmDelete)) {
      try {
        await del(`/api/clients/${id}`);
        toast.success(t.clients.clientDeleted);
        navigate('/clients');
      } catch (error) {
        toast.error(t.common.error);
      }
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('uz-UZ', { style: 'decimal' }).format(amount) + " so'm";
  };

  if (!client) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="client-detail-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/clients')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          data-testid="back-button"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-3xl font-bold text-text-primary flex-1">{client.name}</h1>
        <button
          onClick={() => setEditingClient(true)}
          className="btn-outline flex items-center gap-2"
          data-testid="edit-client-button"
        >
          <Edit size={18} />
          {t.common.edit}
        </button>
        <button
          onClick={handleDeleteClient}
          className="p-2 hover:bg-red-50 rounded-lg transition-colors text-status-error"
          data-testid="delete-client-button"
        >
          <Trash2 size={20} />
        </button>
      </div>

      {/* Client Info Card */}
      <div className="card p-6" data-testid="client-info-card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center">
              <User size={20} className="text-text-secondary" />
            </div>
            <div>
              <p className="text-sm text-text-muted">{t.clients.name}</p>
              <p className="font-medium text-text-primary">{client.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center">
              <Phone size={20} className="text-text-secondary" />
            </div>
            <div>
              <p className="text-sm text-text-muted">{t.clients.phone}</p>
              <p className="font-medium text-text-primary">{client.phone}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center">
              <FileText size={20} className="text-text-secondary" />
            </div>
            <div>
              <p className="text-sm text-text-muted">{t.clients.source}</p>
              <p className="font-medium text-text-primary">{client.source || '-'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center">
              <Clock size={20} className="text-text-secondary" />
            </div>
            <div>
              <p className="text-sm text-text-muted">{t.clients.status}</p>
              <span className={`status-badge status-${client.status}`}>
                {t.statuses[client.status]}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('notes')}
            className={`px-6 py-4 font-medium transition-colors border-b-2 ${
              activeTab === 'notes'
                ? 'border-primary text-text-primary'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
            data-testid="notes-tab"
          >
            <FileText size={18} className="inline mr-2" />
            {t.notes.title} ({notes.length})
          </button>
          <button
            onClick={() => setActiveTab('payments')}
            className={`px-6 py-4 font-medium transition-colors border-b-2 ${
              activeTab === 'payments'
                ? 'border-primary text-text-primary'
                : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
            data-testid="payments-tab"
          >
            <CreditCard size={18} className="inline mr-2" />
            {t.payments.title} ({payments.length})
          </button>
        </div>

        <div className="p-6">
          {/* Notes Tab */}
          {activeTab === 'notes' && (
            <div className="space-y-4" data-testid="notes-section">
              <form onSubmit={handleAddNote} className="flex gap-3">
                <input
                  type="text"
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder={t.notes.placeholder}
                  className="input-field flex-1"
                  data-testid="new-note-input"
                />
                <button type="submit" className="btn-primary" disabled={loading || !newNote.trim()} data-testid="add-note-button">
                  <Plus size={20} />
                </button>
              </form>
              {notes.length === 0 ? (
                <p className="text-text-muted text-center py-8">{t.notes.noNotes}</p>
              ) : (
                <div className="space-y-3">
                  {notes.map((note) => (
                    <div key={note.id} className="p-4 bg-background-subtle rounded-lg" data-testid={`note-${note.id}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-text-primary">{note.text}</p>
                          <p className="text-sm text-text-muted mt-2">
                            {note.author_name} • {formatDate(note.created_at)}
                          </p>
                        </div>
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          className="p-1 hover:bg-red-100 rounded transition-colors"
                          data-testid={`delete-note-${note.id}`}
                        >
                          <Trash2 size={16} className="text-status-error" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Payments Tab */}
          {activeTab === 'payments' && (
            <div className="space-y-4" data-testid="payments-section">
              <button
                onClick={() => setShowPaymentModal(true)}
                className="btn-primary flex items-center gap-2"
                data-testid="add-payment-button"
              >
                <Plus size={20} />
                {t.payments.addPayment}
              </button>
              {payments.length === 0 ? (
                <p className="text-text-muted text-center py-8">{t.payments.noPayments}</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="table-header">
                        <th className="text-left p-4">{t.payments.amount}</th>
                        <th className="text-left p-4">{t.payments.status}</th>
                        <th className="text-left p-4">{t.payments.date}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payments.map((payment) => (
                        <tr key={payment.id} className="table-row" data-testid={`payment-${payment.id}`}>
                          <td className="p-4 font-medium text-text-primary">{formatCurrency(payment.amount)}</td>
                          <td className="p-4">
                            <span className={`status-badge payment-${payment.status}`}>
                              {t.payments[payment.status]}
                            </span>
                          </td>
                          <td className="p-4 text-text-muted">{payment.date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Edit Client Modal */}
      {editingClient && (
        <div className="modal-overlay" onClick={() => setEditingClient(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="edit-client-modal">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold text-text-primary">{t.clients.editClient}</h2>
              <button onClick={() => setEditingClient(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleUpdateClient} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.name}</label>
                <input
                  type="text"
                  value={clientForm.name}
                  onChange={(e) => setClientForm({ ...clientForm, name: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.phone}</label>
                <input
                  type="tel"
                  value={clientForm.phone}
                  onChange={(e) => setClientForm({ ...clientForm, phone: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.source}</label>
                <input
                  type="text"
                  value={clientForm.source}
                  onChange={(e) => setClientForm({ ...clientForm, source: e.target.value })}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.clients.status}</label>
                <select
                  value={clientForm.status}
                  onChange={(e) => setClientForm({ ...clientForm, status: e.target.value })}
                  className="input-field"
                >
                  <option value="new">{t.statuses.new}</option>
                  <option value="contacted">{t.statuses.contacted}</option>
                  <option value="sold">{t.statuses.sold}</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setEditingClient(false)} className="btn-outline flex-1">
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

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="payment-modal">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold text-text-primary">{t.payments.addPayment}</h2>
              <button onClick={() => setShowPaymentModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddPayment} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.amount}</label>
                <input
                  type="number"
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                  className="input-field"
                  required
                  min="0"
                  step="1000"
                  data-testid="payment-amount-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.status}</label>
                <select
                  value={paymentForm.status}
                  onChange={(e) => setPaymentForm({ ...paymentForm, status: e.target.value })}
                  className="input-field"
                  data-testid="payment-status-select"
                >
                  <option value="pending">{t.payments.pending}</option>
                  <option value="paid">{t.payments.paid}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.date}</label>
                <input
                  type="date"
                  value={paymentForm.date}
                  onChange={(e) => setPaymentForm({ ...paymentForm, date: e.target.value })}
                  className="input-field"
                  data-testid="payment-date-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowPaymentModal(false)} className="btn-outline flex-1">
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
