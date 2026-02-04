import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { DollarSign, AlertCircle, CheckCircle, Filter } from 'lucide-react';

export default function PaymentsPage() {
  const { t } = useLanguage();
  const { get, loading } = useApi();
  const [payments, setPayments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadPayments();
  }, [statusFilter]);

  const loadPayments = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const data = await get('/api/payments', params);
      setPayments(data);
    } catch (error) {
      console.error('Failed to load payments:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('uz-UZ', { style: 'decimal' }).format(amount) + " so'm";
  };

  const totalPaid = payments.filter(p => p.status === 'paid').reduce((sum, p) => sum + p.amount, 0);
  const totalPending = payments.filter(p => p.status === 'pending').reduce((sum, p) => sum + p.amount, 0);

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="payments-page">
      <h1 className="text-3xl font-bold text-text-primary">{t.payments.title}</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6" data-testid="total-paid-card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.payments.paidClients}</p>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPaid)}</p>
            </div>
          </div>
        </div>
        <div className="card p-6" data-testid="total-pending-card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <AlertCircle className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-text-muted text-sm font-medium">{t.payments.debtors}</p>
              <p className="text-2xl font-bold text-orange-600">{formatCurrency(totalPending)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex justify-end">
        <div className="relative w-48">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={20} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field pl-10 appearance-none"
            data-testid="payment-status-filter"
          >
            <option value="">{t.clients.allStatuses}</option>
            <option value="paid">{t.payments.paid}</option>
            <option value="pending">{t.payments.pending}</option>
          </select>
        </div>
      </div>

      {/* Payments Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="payments-table">
            <thead>
              <tr className="table-header">
                <th className="text-left p-4">{t.payments.client}</th>
                <th className="text-left p-4">{t.clients.phone}</th>
                <th className="text-left p-4">{t.payments.amount}</th>
                <th className="text-left p-4">{t.payments.status}</th>
                <th className="text-left p-4">{t.payments.date}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="text-center py-12">
                    <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-text-muted">
                    {t.payments.noPayments}
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr key={payment.id} className="table-row" data-testid={`payment-row-${payment.id}`}>
                    <td className="p-4 font-medium text-text-primary">{payment.client_name || '-'}</td>
                    <td className="p-4 text-text-secondary">{payment.client_phone || '-'}</td>
                    <td className="p-4 font-medium text-text-primary">{formatCurrency(payment.amount)}</td>
                    <td className="p-4">
                      <span className={`status-badge payment-${payment.status}`}>
                        {t.payments[payment.status]}
                      </span>
                    </td>
                    <td className="p-4 text-text-muted">{payment.date}</td>
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
