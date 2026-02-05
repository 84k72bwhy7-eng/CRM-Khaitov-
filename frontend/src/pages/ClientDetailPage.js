import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { 
  ArrowLeft, Edit, Trash2, Plus, Phone, User, Clock, FileText, 
  CreditCard, Loader2, X, Bell, Archive, RotateCcw, Upload, Play, Pause, Volume2
} from 'lucide-react';

export default function ClientDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { get, post, put, del, loading } = useApi();
  const audioRef = useRef(null);

  const [client, setClient] = useState(null);
  const [notes, setNotes] = useState([]);
  const [payments, setPayments] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [audioFiles, setAudioFiles] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [activeTab, setActiveTab] = useState('notes');
  const [newNote, setNewNote] = useState('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showReminderModal, setShowReminderModal] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ amount: '', currency: 'USD', status: 'pending', date: '', comment: '' });
  const [editingPayment, setEditingPayment] = useState(null);
  const [reminderForm, setReminderForm] = useState({ text: '', remind_at: '' });
  const [editingClient, setEditingClient] = useState(false);
  const [clientForm, setClientForm] = useState({ name: '', phone: '', source: '', status: '' });
  const [playingAudio, setPlayingAudio] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadClientData();
    loadStatuses();
  }, [id]);

  const loadClientData = async () => {
    try {
      const [clientData, notesData, paymentsData, remindersData, audioData] = await Promise.all([
        get(`/api/clients/${id}`),
        get(`/api/notes/${id}`),
        get(`/api/payments/client/${id}`),
        get('/api/reminders'),
        get(`/api/audio/${id}`)
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
      setReminders(remindersData.filter(r => r.client_id === id));
      setAudioFiles(audioData);
    } catch (error) {
      toast.error(t.common.error);
      navigate('/clients');
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
      const amount = parseFloat(paymentForm.amount);
      if (amount < 0) {
        toast.error(t.payments.invalidAmount);
        return;
      }
      
      if (editingPayment) {
        // Update existing payment
        await put(`/api/payments/${editingPayment.id}`, {
          amount: amount,
          currency: paymentForm.currency,
          status: paymentForm.status,
          date: paymentForm.date || undefined,
          comment: paymentForm.comment || undefined
        });
        toast.success(t.payments.paymentUpdated);
      } else {
        // Create new payment
        await post('/api/payments', {
          client_id: id,
          amount: amount,
          currency: paymentForm.currency,
          status: paymentForm.status,
          date: paymentForm.date || undefined,
          comment: paymentForm.comment || undefined
        });
        toast.success(t.payments.paymentAdded);
      }
      
      setShowPaymentModal(false);
      setEditingPayment(null);
      setPaymentForm({ amount: '', currency: 'USD', status: 'pending', date: '', comment: '' });
      const paymentsData = await get(`/api/payments/client/${id}`);
      setPayments(paymentsData);
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const handleEditPayment = (payment) => {
    setEditingPayment(payment);
    setPaymentForm({
      amount: payment.amount.toString(),
      currency: payment.currency || 'USD',
      status: payment.status || 'pending',
      date: payment.date || '',
      comment: payment.comment || ''
    });
    setShowPaymentModal(true);
  };

  const handleDeletePayment = async (paymentId) => {
    if (!window.confirm(t.common.confirmDelete)) return;
    try {
      await del(`/api/payments/${paymentId}`);
      toast.success(t.payments.paymentDeleted);
      const paymentsData = await get(`/api/payments/client/${id}`);
      setPayments(paymentsData);
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleAddReminder = async (e) => {
    e.preventDefault();
    try {
      await post('/api/reminders', {
        client_id: id,
        text: reminderForm.text,
        remind_at: new Date(reminderForm.remind_at).toISOString()
      });
      toast.success(t.reminders.reminderCreated);
      setShowReminderModal(false);
      setReminderForm({ text: '', remind_at: '' });
      loadClientData();
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleCompleteReminder = async (reminderId) => {
    try {
      await put(`/api/reminders/${reminderId}`, { is_completed: true });
      toast.success(t.reminders.reminderUpdated);
      loadClientData();
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleDeleteReminder = async (reminderId) => {
    try {
      await del(`/api/reminders/${reminderId}`);
      toast.success(t.reminders.reminderDeleted);
      loadClientData();
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

  const handleArchiveClient = async () => {
    try {
      await post(`/api/clients/${id}/archive`);
      toast.success(t.clients.clientUpdated);
      navigate('/clients');
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const handleRestoreClient = async () => {
    try {
      await post(`/api/clients/${id}/restore`);
      toast.success(t.clients.clientUpdated);
      loadClientData();
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

  const handleAudioUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp3', 'audio/webm'];
    if (!allowedTypes.includes(file.type)) {
      toast.error(t.audio.invalidType);
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('client_id', id);

    try {
      const response = await fetch('/api/audio/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('crm_token')}`
        },
        body: formData
      });
      
      if (response.ok) {
        toast.success(t.audio.uploadSuccess);
        const audioData = await get(`/api/audio/${id}`);
        setAudioFiles(audioData);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      toast.error(t.common.error);
    } finally {
      setUploading(false);
    }
  };

  const handlePlayAudio = (audioId) => {
    if (playingAudio === audioId) {
      audioRef.current?.pause();
      setPlayingAudio(null);
    } else {
      setPlayingAudio(audioId);
    }
  };

  const handleDeleteAudio = async (audioId) => {
    try {
      await del(`/api/audio/${audioId}`);
      toast.success(t.audio.deleteSuccess);
      setAudioFiles(audioFiles.filter(a => a.id !== audioId));
    } catch (error) {
      toast.error(t.common.error);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('uz-UZ', { 
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (currency === 'USD') {
      return '$' + new Intl.NumberFormat('en-US').format(amount);
    }
    return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const isOverdue = (dateStr) => {
    return new Date(dateStr) < new Date();
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
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <button
          onClick={() => navigate('/clients')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors self-start"
          data-testid="back-button"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-2xl lg:text-3xl font-bold text-text-primary flex-1">{client.name}</h1>
        <div className="flex flex-wrap gap-2">
          {client.is_archived ? (
            <button
              onClick={handleRestoreClient}
              className="btn-outline flex items-center gap-2 text-sm"
              data-testid="restore-client-button"
            >
              <RotateCcw size={16} />
              {t.clients.restore}
            </button>
          ) : (
            <button
              onClick={handleArchiveClient}
              className="btn-outline flex items-center gap-2 text-sm"
              data-testid="archive-client-button"
            >
              <Archive size={16} />
              {t.clients.archive}
            </button>
          )}
          <button
            onClick={() => setEditingClient(true)}
            className="btn-outline flex items-center gap-2 text-sm"
            data-testid="edit-client-button"
          >
            <Edit size={16} />
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
      </div>

      {/* Archived Badge */}
      {client.is_archived && (
        <div className="card p-4 bg-gray-100 border-gray-300">
          <p className="text-gray-600 font-medium">{t.clients.archived}</p>
        </div>
      )}

      {/* Client Info Card */}
      <div className="card p-4 lg:p-6" data-testid="client-info-card">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center flex-shrink-0">
              <User size={20} className="text-text-secondary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-text-muted">{t.clients.name}</p>
              <p className="font-medium text-text-primary truncate">{client.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center flex-shrink-0">
              <Phone size={20} className="text-text-secondary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-text-muted">{t.clients.phone}</p>
              <p className="font-medium text-text-primary truncate">{client.phone}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center flex-shrink-0">
              <FileText size={20} className="text-text-secondary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-text-muted">{t.clients.source}</p>
              <p className="font-medium text-text-primary truncate">{client.source || '-'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background-subtle rounded-lg flex items-center justify-center flex-shrink-0">
              <Clock size={20} className="text-text-secondary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-text-muted">{t.clients.status}</p>
              <span className={`status-badge status-${client.status}`}>
                {t.statuses[client.status] || client.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="flex overflow-x-auto border-b border-border">
          {['notes', 'payments', 'reminders', 'audio'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 lg:px-6 py-3 lg:py-4 font-medium transition-colors border-b-2 whitespace-nowrap text-sm lg:text-base ${
                activeTab === tab
                  ? 'border-primary text-text-primary'
                  : 'border-transparent text-text-muted hover:text-text-secondary'
              }`}
              data-testid={`${tab}-tab`}
            >
              {tab === 'notes' && <FileText size={16} className="inline mr-2" />}
              {tab === 'payments' && <CreditCard size={16} className="inline mr-2" />}
              {tab === 'reminders' && <Bell size={16} className="inline mr-2" />}
              {tab === 'audio' && <Volume2 size={16} className="inline mr-2" />}
              {t[tab]?.title || tab} ({tab === 'notes' ? notes.length : tab === 'payments' ? payments.length : tab === 'reminders' ? reminders.length : audioFiles.length})
            </button>
          ))}
        </div>

        <div className="p-4 lg:p-6">
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
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-text-primary break-words">{note.text}</p>
                          <p className="text-sm text-text-muted mt-2">
                            {note.author_name} • {formatDate(note.created_at)}
                          </p>
                        </div>
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          className="p-1 hover:bg-red-100 rounded transition-colors flex-shrink-0"
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
                onClick={() => {
                  setEditingPayment(null);
                  setPaymentForm({ amount: '', currency: 'USD', status: 'pending', date: '', comment: '' });
                  setShowPaymentModal(true);
                }}
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
                  <table className="w-full min-w-[500px]">
                    <thead>
                      <tr className="table-header">
                        <th className="text-left p-3 lg:p-4">{t.payments.amount}</th>
                        <th className="text-left p-3 lg:p-4">{t.payments.status}</th>
                        <th className="text-left p-3 lg:p-4">{t.payments.date}</th>
                        <th className="text-left p-3 lg:p-4">{t.payments.comment}</th>
                        <th className="text-left p-3 lg:p-4">{t.common.actions}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payments.map((payment) => (
                        <tr key={payment.id} className="table-row" data-testid={`payment-${payment.id}`}>
                          <td className="p-3 lg:p-4 font-medium text-text-primary">{formatCurrency(payment.amount, payment.currency)}</td>
                          <td className="p-3 lg:p-4">
                            <span className={`status-badge payment-${payment.status}`}>
                              {t.payments[payment.status]}
                            </span>
                          </td>
                          <td className="p-3 lg:p-4 text-text-muted">{payment.date}</td>
                          <td className="p-3 lg:p-4 text-text-muted text-sm max-w-[150px] truncate">
                            {payment.comment || '-'}
                          </td>
                          <td className="p-3 lg:p-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleEditPayment(payment)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title={t.common.edit}
                                data-testid={`edit-payment-${payment.id}`}
                              >
                                <Edit size={16} className="text-text-secondary" />
                              </button>
                              <button
                                onClick={() => handleDeletePayment(payment.id)}
                                className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                                title={t.common.delete}
                                data-testid={`delete-payment-${payment.id}`}
                              >
                                <Trash2 size={16} className="text-status-error" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Reminders Tab */}
          {activeTab === 'reminders' && (
            <div className="space-y-4" data-testid="reminders-section">
              <button
                onClick={() => setShowReminderModal(true)}
                className="btn-primary flex items-center gap-2"
                data-testid="add-reminder-button"
              >
                <Plus size={20} />
                {t.reminders.addReminder}
              </button>
              {reminders.length === 0 ? (
                <p className="text-text-muted text-center py-8">{t.reminders.noReminders}</p>
              ) : (
                <div className="space-y-3">
                  {reminders.map((reminder) => (
                    <div 
                      key={reminder.id} 
                      className={`p-4 rounded-lg border ${
                        reminder.is_completed 
                          ? 'bg-gray-50 border-gray-200' 
                          : isOverdue(reminder.remind_at) 
                            ? 'bg-red-50 border-red-200' 
                            : 'bg-background-subtle border-border'
                      }`}
                      data-testid={`reminder-${reminder.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className={`font-medium ${reminder.is_completed ? 'line-through text-text-muted' : 'text-text-primary'}`}>
                            {reminder.text}
                          </p>
                          <p className={`text-sm mt-1 ${isOverdue(reminder.remind_at) && !reminder.is_completed ? 'text-red-600' : 'text-text-muted'}`}>
                            <Clock size={14} className="inline mr-1" />
                            {formatDateTime(reminder.remind_at)}
                            {isOverdue(reminder.remind_at) && !reminder.is_completed && (
                              <span className="ml-2 text-red-600 font-medium">({t.reminders.overdue})</span>
                            )}
                          </p>
                        </div>
                        <div className="flex gap-2 flex-shrink-0">
                          {!reminder.is_completed && (
                            <button
                              onClick={() => handleCompleteReminder(reminder.id)}
                              className="p-1 hover:bg-green-100 rounded transition-colors text-green-600"
                              title={t.reminders.markComplete}
                            >
                              ✓
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteReminder(reminder.id)}
                            className="p-1 hover:bg-red-100 rounded transition-colors"
                          >
                            <Trash2 size={16} className="text-status-error" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Audio Tab */}
          {activeTab === 'audio' && (
            <div className="space-y-4" data-testid="audio-section">
              <label className="btn-primary flex items-center gap-2 cursor-pointer w-fit">
                {uploading ? <Loader2 size={20} className="animate-spin" /> : <Upload size={20} />}
                {t.audio.upload}
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleAudioUpload}
                  className="hidden"
                  disabled={uploading}
                />
              </label>
              {audioFiles.length === 0 ? (
                <p className="text-text-muted text-center py-8">{t.audio.noFiles}</p>
              ) : (
                <div className="space-y-3">
                  {audioFiles.map((audio) => (
                    <div key={audio.id} className="p-4 bg-background-subtle rounded-lg" data-testid={`audio-${audio.id}`}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <button
                            onClick={() => handlePlayAudio(audio.id)}
                            className="w-10 h-10 bg-primary rounded-full flex items-center justify-center flex-shrink-0"
                          >
                            {playingAudio === audio.id ? <Pause size={18} className="text-black" /> : <Play size={18} className="text-black ml-0.5" />}
                          </button>
                          <div className="min-w-0">
                            <p className="font-medium text-text-primary truncate">{audio.original_name}</p>
                            <p className="text-sm text-text-muted">
                              {formatFileSize(audio.size)} • {t.audio.uploadedBy}: {audio.uploader_name}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteAudio(audio.id)}
                          className="p-2 hover:bg-red-100 rounded transition-colors flex-shrink-0"
                        >
                          <Trash2 size={16} className="text-status-error" />
                        </button>
                      </div>
                      {playingAudio === audio.id && (
                        <audio
                          ref={audioRef}
                          src={`/api/audio/file/${audio.id}`}
                          autoPlay
                          controls
                          className="w-full mt-3"
                          onEnded={() => setPlayingAudio(null)}
                        />
                      )}
                    </div>
                  ))}
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
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">{t.clients.editClient}</h2>
              <button onClick={() => setEditingClient(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleUpdateClient} className="p-4 lg:p-6 space-y-4">
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
                  {statuses.map((s) => (
                    <option key={s.id} value={s.name}>{t.statuses[s.name] || s.name}</option>
                  ))}
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
        <div className="modal-overlay" onClick={() => { setShowPaymentModal(false); setEditingPayment(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="payment-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">
                {editingPayment ? t.payments.editPayment : t.payments.addPayment}
              </h2>
              <button onClick={() => { setShowPaymentModal(false); setEditingPayment(null); }} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddPayment} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.amount}</label>
                <input
                  type="number"
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                  className="input-field"
                  required
                  min="0"
                  step="0.01"
                  data-testid="payment-amount-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.payments.currency}</label>
                <select
                  value={paymentForm.currency}
                  onChange={(e) => setPaymentForm({ ...paymentForm, currency: e.target.value })}
                  className="input-field"
                  data-testid="payment-currency-select"
                >
                  <option value="USD">USD ($)</option>
                  <option value="UZS">UZS (so'm)</option>
                </select>
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
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.payments.comment} <span className="text-text-muted font-normal">({t.common.optional})</span>
                </label>
                <textarea
                  value={paymentForm.comment}
                  onChange={(e) => setPaymentForm({ ...paymentForm, comment: e.target.value })}
                  className="input-field min-h-[80px] resize-y"
                  placeholder={t.payments.commentPlaceholder}
                  data-testid="payment-comment-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => { setShowPaymentModal(false); setEditingPayment(null); }} className="btn-outline flex-1">
                  {t.common.cancel}
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-payment-button">
                  {loading && <Loader2 size={18} className="animate-spin" />}
                  {t.common.save}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reminder Modal */}
      {showReminderModal && (
        <div className="modal-overlay" onClick={() => setShowReminderModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="reminder-modal">
            <div className="p-4 lg:p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-lg lg:text-xl font-bold text-text-primary">{t.reminders.addReminder}</h2>
              <button onClick={() => setShowReminderModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddReminder} className="p-4 lg:p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.reminders.reminderText}</label>
                <input
                  type="text"
                  value={reminderForm.text}
                  onChange={(e) => setReminderForm({ ...reminderForm, text: e.target.value })}
                  className="input-field"
                  required
                  data-testid="reminder-text-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.reminders.remindAt}</label>
                <input
                  type="datetime-local"
                  value={reminderForm.remind_at}
                  onChange={(e) => setReminderForm({ ...reminderForm, remind_at: e.target.value })}
                  className="input-field"
                  required
                  data-testid="reminder-datetime-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowReminderModal(false)} className="btn-outline flex-1">
                  {t.common.cancel}
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-reminder-button">
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
