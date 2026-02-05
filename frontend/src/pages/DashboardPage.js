import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { Users, UserPlus, DollarSign, TrendingUp, TrendingDown, Clock, FileText, Bell, AlertTriangle, BarChart3, PieChart } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, LineChart, Line, Legend } from 'recharts';

export default function DashboardPage() {
  const { t } = useLanguage();
  const { isAdmin } = useAuth();
  const { get, loading } = useApi();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentClients, setRecentClients] = useState([]);
  const [recentNotes, setRecentNotes] = useState([]);
  const [overdueReminders, setOverdueReminders] = useState([]);
  const [managerStats, setManagerStats] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, clientsData, notesData, remindersData] = await Promise.all([
        get('/api/dashboard/stats'),
        get('/api/dashboard/recent-clients'),
        get('/api/dashboard/recent-notes'),
        get('/api/reminders/overdue')
      ]);
      setStats(statsData);
      setRecentClients(clientsData);
      setRecentNotes(notesData);
      setOverdueReminders(remindersData);

      if (isAdmin) {
        const managerData = await get('/api/dashboard/manager-stats');
        setManagerStats(managerData);
        
        // Load analytics data
        const analyticsData = await get('/api/dashboard/analytics');
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (currency === 'USD') {
      return '$' + new Intl.NumberFormat('en-US').format(amount);
    }
    return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
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

      {/* Overdue Reminders Alert */}
      {overdueReminders.length > 0 && (
        <div className="card p-4 bg-red-50 border-red-200" data-testid="overdue-reminders-alert">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={24} />
            <div className="flex-1">
              <p className="font-medium text-red-800">{t.dashboard.overdueReminders}: {overdueReminders.length}</p>
              <div className="mt-2 space-y-1">
                {overdueReminders.slice(0, 3).map((reminder) => (
                  <p key={reminder.id} className="text-sm text-red-600">
                    • {reminder.client_name}: {reminder.text}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {/* Today's Leads */}
        <div className="card p-4 lg:p-6" data-testid="stat-todays-leads">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 lg:w-12 lg:h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <UserPlus className="text-blue-600" size={20} />
            </div>
            <div className="min-w-0">
              <p className="text-text-muted text-xs lg:text-sm font-medium truncate">{t.dashboard.todaysLeads}</p>
              <p className="text-2xl lg:text-3xl font-bold text-text-primary">{stats?.todays_leads || 0}</p>
            </div>
          </div>
        </div>

        {/* Total Clients */}
        <div className="card p-4 lg:p-6" data-testid="stat-total-clients">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 lg:w-12 lg:h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Users className="text-purple-600" size={20} />
            </div>
            <div className="min-w-0">
              <p className="text-text-muted text-xs lg:text-sm font-medium truncate">{t.dashboard.totalClients}</p>
              <p className="text-2xl lg:text-3xl font-bold text-text-primary">{stats?.total_clients || 0}</p>
            </div>
          </div>
        </div>

        {/* Sales Count */}
        <div className="card p-4 lg:p-6" data-testid="stat-sales-count">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 lg:w-12 lg:h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div className="min-w-0">
              <p className="text-text-muted text-xs lg:text-sm font-medium truncate">{t.dashboard.salesCount}</p>
              <p className="text-2xl lg:text-3xl font-bold text-text-primary">{stats?.sold_count || 0}</p>
            </div>
          </div>
        </div>

        {/* Total Paid */}
        <div className="card p-4 lg:p-6" data-testid="stat-total-paid">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 lg:w-12 lg:h-12 bg-primary/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <DollarSign className="text-primary-foreground" size={20} />
            </div>
            <div className="min-w-0">
              <p className="text-text-muted text-xs lg:text-sm font-medium truncate">{t.dashboard.totalPaid}</p>
              <p className="text-xl lg:text-2xl font-bold text-text-primary">{formatCurrency(stats?.total_paid || 0, stats?.currency)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 lg:gap-6">
        <div className="card p-4 lg:p-6 border-l-4 border-l-blue-500" data-testid="status-new">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.newLeads}</p>
          <p className="text-2xl lg:text-3xl font-bold text-blue-600">{stats?.new_count || 0}</p>
        </div>
        <div className="card p-4 lg:p-6 border-l-4 border-l-yellow-500" data-testid="status-contacted">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.contacted}</p>
          <p className="text-2xl lg:text-3xl font-bold text-yellow-600">{stats?.contacted_count || 0}</p>
        </div>
        <div className="card p-4 lg:p-6 border-l-4 border-l-green-500" data-testid="status-sold">
          <p className="text-text-muted text-sm font-medium">{t.dashboard.sold}</p>
          <p className="text-2xl lg:text-3xl font-bold text-green-600">{stats?.sold_count || 0}</p>
        </div>
      </div>

      {/* Pending Payments Alert */}
      {stats?.total_pending > 0 && (
        <div className="card p-4 lg:p-6 bg-orange-50 border-orange-200" data-testid="pending-alert">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 lg:w-12 lg:h-12 bg-orange-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Clock className="text-orange-600" size={20} />
            </div>
            <div>
              <p className="text-orange-800 font-medium">{t.dashboard.totalPending}</p>
              <p className="text-xl lg:text-2xl font-bold text-orange-600">{formatCurrency(stats.total_pending, stats?.currency)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Manager Stats (Admin Only) */}
      {isAdmin && managerStats.length > 0 && (
        <div className="card" data-testid="manager-stats-card">
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
              <TrendingUp size={20} />
              {t.dashboard.managerStats}
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="table-header">
                  <th className="text-left p-3 lg:p-4">{t.users.name}</th>
                  <th className="text-left p-3 lg:p-4">{t.dashboard.deals}</th>
                  <th className="text-left p-3 lg:p-4">{t.dashboard.revenue}</th>
                  <th className="text-left p-3 lg:p-4">{t.dashboard.totalClients}</th>
                </tr>
              </thead>
              <tbody>
                {managerStats.map((manager) => (
                  <tr key={manager.id} className="table-row">
                    <td className="p-3 lg:p-4 font-medium">{manager.name}</td>
                    <td className="p-3 lg:p-4">{manager.sold_count}</td>
                    <td className="p-3 lg:p-4 font-medium text-green-600">{formatCurrency(manager.total_revenue)}</td>
                    <td className="p-3 lg:p-4">{manager.total_clients}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analytics Section (Admin Only) */}
      {isAdmin && analytics && (
        <>
          {/* Month-over-Month Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6" data-testid="analytics-summary">
            <div className="card p-4 lg:p-6">
              <p className="text-text-muted text-sm">{t.dashboard.revenue} ({analytics.currency})</p>
              <p className="text-2xl font-bold text-text-primary">
                {formatCurrency(analytics.summary?.total_revenue || 0, analytics.currency)}
              </p>
              <div className={`flex items-center gap-1 mt-2 text-sm ${analytics.summary?.revenue_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analytics.summary?.revenue_change_pct >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span>{analytics.summary?.revenue_change_pct >= 0 ? '+' : ''}{analytics.summary?.revenue_change_pct?.toFixed(1)}%</span>
                <span className="text-text-muted">{t.dashboard.monthComparison}</span>
              </div>
            </div>
            <div className="card p-4 lg:p-6">
              <p className="text-text-muted text-sm">{t.dashboard.deals}</p>
              <p className="text-2xl font-bold text-text-primary">{analytics.summary?.total_deals || 0}</p>
              <div className={`flex items-center gap-1 mt-2 text-sm ${analytics.summary?.deals_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analytics.summary?.deals_change_pct >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span>{analytics.summary?.deals_change_pct >= 0 ? '+' : ''}{analytics.summary?.deals_change_pct?.toFixed(1)}%</span>
                <span className="text-text-muted">{t.dashboard.monthComparison}</span>
              </div>
            </div>
            <div className="card p-4 lg:p-6">
              <p className="text-text-muted text-sm">{t.dashboard.newLeads}</p>
              <p className="text-2xl font-bold text-text-primary">{analytics.summary?.total_leads || 0}</p>
            </div>
            <div className="card p-4 lg:p-6">
              <p className="text-text-muted text-sm">{analytics.summary?.revenue_change_pct >= 0 ? t.dashboard.growth : t.dashboard.decline}</p>
              <p className={`text-2xl font-bold ${analytics.summary?.revenue_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analytics.summary?.revenue_change_pct >= 0 ? '+' : ''}{formatCurrency(analytics.summary?.revenue_change || 0, analytics.currency)}
              </p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
            {/* Monthly Sales Chart */}
            <div className="card" data-testid="monthly-chart">
              <div className="p-4 lg:p-6 border-b border-border">
                <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                  <BarChart3 size={20} />
                  {t.dashboard.monthlyStats}
                </h2>
              </div>
              <div className="p-4 lg:p-6">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics.monthly_data || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis 
                      dataKey="month_name" 
                      tick={{ fontSize: 12, fill: '#6B7280' }}
                      axisLine={{ stroke: '#E5E7EB' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6B7280' }}
                      axisLine={{ stroke: '#E5E7EB' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [
                        name === 'revenue' ? formatCurrency(value, analytics.currency) : value,
                        name === 'revenue' ? t.dashboard.revenue : name === 'sold_count' ? t.dashboard.deals : t.dashboard.newLeads
                      ]}
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                    />
                    <Legend />
                    <Bar dataKey="sold_count" name={t.dashboard.deals} fill="#FACC15" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="new_leads" name={t.dashboard.newLeads} fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Revenue Trend Chart */}
            <div className="card" data-testid="revenue-chart">
              <div className="p-4 lg:p-6 border-b border-border">
                <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                  <TrendingUp size={20} />
                  {t.dashboard.revenue}
                </h2>
              </div>
              <div className="p-4 lg:p-6">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analytics.monthly_data || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis 
                      dataKey="month_name" 
                      tick={{ fontSize: 12, fill: '#6B7280' }}
                      axisLine={{ stroke: '#E5E7EB' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: '#6B7280' }}
                      axisLine={{ stroke: '#E5E7EB' }}
                      tickFormatter={(value) => analytics.currency === 'USD' ? `$${value.toLocaleString()}` : value.toLocaleString()}
                    />
                    <Tooltip 
                      formatter={(value) => [formatCurrency(value, analytics.currency), t.dashboard.revenue]}
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="revenue" 
                      stroke="#22C55E" 
                      strokeWidth={3}
                      dot={{ fill: '#22C55E', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Tariff Stats */}
          {analytics.tariff_stats && analytics.tariff_stats.length > 0 && (
            <div className="card" data-testid="tariff-stats">
              <div className="p-4 lg:p-6 border-b border-border">
                <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
                  <PieChart size={20} />
                  {t.dashboard.tariffStats}
                </h2>
              </div>
              <div className="p-4 lg:p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Pie Chart */}
                  <div className="flex justify-center">
                    <ResponsiveContainer width="100%" height={250}>
                      <RechartsPie>
                        <Pie
                          data={analytics.tariff_stats}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="sold_count"
                          nameKey="name"
                          label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                        >
                          {analytics.tariff_stats.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={['#FACC15', '#3B82F6', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899'][index % 6]} 
                            />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value, name, props) => [
                            `${value} ${t.dashboard.deals.toLowerCase()} (${formatCurrency(props.payload.revenue, analytics.currency)})`,
                            props.payload.name
                          ]}
                        />
                      </RechartsPie>
                    </ResponsiveContainer>
                  </div>
                  {/* Stats Table */}
                  <div className="space-y-3">
                    {analytics.tariff_stats.map((tariff, index) => (
                      <div 
                        key={index}
                        className="flex items-center justify-between p-3 bg-background-subtle rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: ['#FACC15', '#3B82F6', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899'][index % 6] }}
                          />
                          <div>
                            <p className="font-medium text-text-primary">{tariff.name}</p>
                            <p className="text-sm text-text-muted">{formatCurrency(tariff.price, analytics.currency)} / {t.clients.tariff.toLowerCase()}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-text-primary">{tariff.sold_count}</p>
                          <p className="text-sm text-green-600">{formatCurrency(tariff.revenue, analytics.currency)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Recent Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
        {/* Recent Clients */}
        <div className="card" data-testid="recent-clients-card">
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
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
                    onClick={() => navigate(`/clients/${client.id}`)}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-background-subtle transition-colors cursor-pointer"
                    data-testid={`recent-client-${client.id}`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-text-primary truncate">{client.name}</p>
                      <p className="text-sm text-text-muted truncate">{client.phone}</p>
                    </div>
                    <span className={`status-badge status-${client.status} ml-2 flex-shrink-0`}>
                      {t.statuses[client.status] || client.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Notes */}
        <div className="card" data-testid="recent-notes-card">
          <div className="p-4 lg:p-6 border-b border-border">
            <h2 className="text-lg lg:text-xl font-bold text-text-primary flex items-center gap-2">
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
                      <p className="font-medium text-text-primary text-sm truncate">{note.client_name}</p>
                      <p className="text-xs text-text-muted flex-shrink-0 ml-2">{formatDate(note.created_at)}</p>
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
