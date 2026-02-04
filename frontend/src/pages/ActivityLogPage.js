import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { History, Filter } from 'lucide-react';

export default function ActivityLogPage() {
  const { t } = useLanguage();
  const { get, loading } = useApi();
  const [activities, setActivities] = useState([]);
  const [entityFilter, setEntityFilter] = useState('');

  useEffect(() => {
    loadActivities();
  }, [entityFilter]);

  const loadActivities = async () => {
    try {
      const params = entityFilter ? { entity_type: entityFilter, limit: 100 } : { limit: 100 };
      const data = await get('/api/activity-log', params);
      setActivities(data);
    } catch (error) {
      console.error('Failed to load activities:', error);
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString('uz-UZ', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'create': return 'bg-green-100 text-green-800';
      case 'update': return 'bg-blue-100 text-blue-800';
      case 'delete': return 'bg-red-100 text-red-800';
      case 'archive': return 'bg-gray-100 text-gray-800';
      case 'restore': return 'bg-purple-100 text-purple-800';
      case 'upload': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getEntityIcon = (entityType) => {
    switch (entityType) {
      case 'client': return '👤';
      case 'payment': return '💰';
      case 'note': return '📝';
      case 'user': return '👥';
      case 'status': return '🏷️';
      case 'reminder': return '🔔';
      case 'audio': return '🎵';
      default: return '📋';
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="activity-log-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl lg:text-3xl font-bold text-text-primary flex items-center gap-2">
          <History size={28} />
          {t.activityLog.title}
        </h1>
        <div className="relative w-full sm:w-48">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="input-field pl-10 appearance-none"
            data-testid="entity-filter"
          >
            <option value="">{t.common.all}</option>
            <option value="client">{t.clients.title}</option>
            <option value="payment">{t.payments.title}</option>
            <option value="user">{t.users.title}</option>
            <option value="note">{t.notes.title}</option>
            <option value="status">{t.statuses.title}</option>
            <option value="reminder">{t.reminders.title}</option>
          </select>
        </div>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12 text-text-muted">
            No activity found
          </div>
        ) : (
          <div className="divide-y divide-border">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="p-4 lg:p-6 hover:bg-background-subtle transition-colors"
                data-testid={`activity-${activity.id}`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-2xl">{getEntityIcon(activity.entity_type)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`status-badge ${getActionColor(activity.action)}`}>
                          {t.activityLog.actions[activity.action] || activity.action}
                        </span>
                        <span className="font-medium text-text-primary capitalize">
                          {activity.entity_type}
                        </span>
                      </div>
                      <p className="text-sm text-text-secondary mt-1">
                        {t.activityLog.user}: <span className="font-medium">{activity.user_name}</span>
                      </p>
                      {activity.details && Object.keys(activity.details).length > 0 && (
                        <p className="text-sm text-text-muted mt-1 truncate">
                          {JSON.stringify(activity.details)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-text-muted whitespace-nowrap">
                    {formatDateTime(activity.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
