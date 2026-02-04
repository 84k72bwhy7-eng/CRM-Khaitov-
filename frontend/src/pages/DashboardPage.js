import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { Users, UserPlus, DollarSign, TrendingUp, Clock, FileText } from 'lucide-react';

export default function DashboardPage() {
  const { t } = useLanguage();
  const { get, loading } = useApi();
  const [stats, setStats] = useState(null);
  const [recentClients, setRecentClients] = useState([]);
  const [recentNotes, setRecentNotes] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, clientsData, notesData] = await Promise.all([
        get('/api/dashboard/stats'),
        get('/api/dashboard/recent-clients'),
        get('/api/dashboard/recent-notes')
      ]);
      setStats(statsData);
      setRecentClients(clientsData);
      setRecentNotes(notesData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('uz-UZ', { style: 'decimal' }).format(amount) + ' so\'m';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn" data-testid="dashboard-page">
      <h1 className="text-3xl font-bold text-text-primary">{t.dashboard.title}</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Today's Leads */}
        <div className="card p-6" data-testid="stat-todays-leads">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <UserPlus className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.dashboard.todaysLeads}</p>
              <p className="text-3xl font-bold text-text-primary">{stats?.todays_leads || 0}</p>
            </div>
          </div>
        </div>

        {/* Total Clients */}
        <div className="card p-6" data-testid="stat-total-clients">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <Users className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.dashboard.totalClients}</p>
              <p className="text-3xl font-bold text-text-primary">{stats?.total_clients || 0}</p>
            </div>
          </div>
        </div>

        {/* Sales Count */}
        <div className="card p-6" data-testid="stat-sales-count">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.dashboard.salesCount}</p>
              <p className="text-3xl font-bold text-text-primary">{stats?.sold_count || 0}</p>
            </div>
          </div>
        </div>

        {/* Total Paid */}
        <div className="card p-6" data-testid="stat-total-paid">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary/20 rounded-xl flex items-center justify-center">
              <DollarSign className="text-primary-foreground" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.dashboard.totalPaid}</p>
              <p className="text-2xl font-bold text-text-primary">{formatCurrency(stats?.total_paid || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6 border-l-4 border-l-blue-500" data-testid="status-new">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.newLeads}</p>
          <p className="text-3xl font-bold text-blue-600">{stats?.new_count || 0}</p>
        </div>
        <div className="card p-6 border-l-4 border-l-yellow-500" data-testid="status-contacted">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.contacted}</p>
          <p className="text-3xl font-bold text-yellow-600">{stats?.contacted_count || 0}</p>
        </div>
        <div className="card p-6 border-l-4 border-l-green-500" data-testid="status-sold">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.sold}</p>
          <p className="text-3xl font-bold text-green-600">{stats?.sold_count || 0}</p>
        </div>
      </div>

      {/* Pending Payments Alert */}
      {stats?.total_pending > 0 && (
        <div className="card p-6 bg-orange-50 border-orange-200" data-testid="pending-alert">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <Clock className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-orange-800 font-medium">{t.dashboard.totalPending}</p>
              <p className="text-2xl font-bold text-orange-600">{formatCurrency(stats.total_pending)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Clients */}
        <div className="card" data-testid="recent-clients-card">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <Users size={20} />
              {t.dashboard.recentClients}
            </h2>
          </div>
          <div className="p-4">
            {recentClients.length === 0 ? (
              <p className="text-text-muted text-center py-8">{t.clients.noClients}</p>
            ) : (
              <div className="space-y-3">
                {recentClients.map((client) => (
                  <div
                    key={client.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-background-subtle transition-colors"
                    data-testid={`recent-client-${client.id}`}
                  >
                    <div>
                      <p className="font-medium text-text-primary">{client.name}</p>
                      <p className="text-sm text-text-muted">{client.phone}</p>
                    </div>
                    <span className={`status-badge status-${client.status}`}>
                      {t.statuses[client.status]}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Notes */}
        <div className="card" data-testid="recent-notes-card">
          <div className="p-6 border-b border-border">
            <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <FileText size={20} />
              {t.dashboard.recentNotes}
            </h2>
          </div>
          <div className="p-4">
            {recentNotes.length === 0 ? (
              <p className="text-text-muted text-center py-8">{t.notes.noNotes}</p>
            ) : (
              <div className="space-y-3">
                {recentNotes.map((note) => (
                  <div
                    key={note.id}
                    className="p-3 rounded-lg bg-background-subtle"
                    data-testid={`recent-note-${note.id}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-text-primary text-sm">{note.client_name}</p>
                      <p className="text-xs text-text-muted">{formatDate(note.created_at)}</p>
                    </div>
                    <p className="text-text-secondary text-sm line-clamp-2">{note.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
