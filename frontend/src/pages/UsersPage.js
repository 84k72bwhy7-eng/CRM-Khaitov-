import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useApi } from '../hooks/useApi';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, X, Loader2, UserCog } from 'lucide-react';

export default function UsersPage() {
  const { t } = useLanguage();
  const { get, post, put, del, loading } = useApi();
  const [users, setUsers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', password: '', role: 'manager' });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await get('/api/users');
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        const updateData = { ...formData };
        if (!updateData.password) delete updateData.password;
        await put(`/api/users/${editingUser.id}`, updateData);
        toast.success(t.users.userUpdated);
      } else {
        await post('/api/users', formData);
        toast.success(t.users.userCreated);
      }
      setShowModal(false);
      setEditingUser(null);
      setFormData({ name: '', email: '', phone: '', password: '', role: 'manager' });
      loadUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || t.common.error);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      name: user.name,
      email: user.email,
      phone: user.phone,
      password: '',
      role: user.role
    });
    setShowModal(true);
  };

  const handleDelete = async (user) => {
    if (window.confirm(t.users.confirmDelete)) {
      try {
        await del(`/api/users/${user.id}`);
        toast.success(t.users.userDeleted);
        loadUsers();
      } catch (error) {
        toast.error(error.response?.data?.detail || t.common.error);
      }
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="users-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h1 className="text-3xl font-bold text-text-primary">{t.users.title}</h1>
        <button
          onClick={() => {
            setEditingUser(null);
            setFormData({ name: '', email: '', phone: '', password: '', role: 'manager' });
            setShowModal(true);
          }}
          className="btn-primary flex items-center gap-2"
          data-testid="add-user-button"
        >
          <Plus size={20} />
          {t.users.addUser}
        </button>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="users-table">
            <thead>
              <tr className="table-header">
                <th className="text-left p-4">{t.users.name}</th>
                <th className="text-left p-4">{t.users.email}</th>
                <th className="text-left p-4">{t.users.phone}</th>
                <th className="text-left p-4">{t.users.role}</th>
                <th className="text-left p-4">{t.clients.actions}</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-text-muted">
                    {t.users.noUsers}
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id} className="table-row" data-testid={`user-row-${user.id}`}>
                    <td className="p-4 font-medium text-text-primary">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-black">{user.name[0]}</span>
                        </div>
                        {user.name}
                      </div>
                    </td>
                    <td className="p-4 text-text-secondary">{user.email}</td>
                    <td className="p-4 text-text-secondary">{user.phone}</td>
                    <td className="p-4">
                      <span className={`status-badge ${
                        user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {user.role === 'admin' ? t.users.admin : t.users.manager}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEdit(user)}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          data-testid={`edit-user-${user.id}`}
                        >
                          <Edit size={18} className="text-text-secondary" />
                        </button>
                        <button
                          onClick={() => handleDelete(user)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                          data-testid={`delete-user-${user.id}`}
                        >
                          <Trash2 size={18} className="text-status-error" />
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
          <div className="modal-content" onClick={(e) => e.stopPropagation()} data-testid="user-modal">
            <div className="p-6 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                <UserCog size={24} />
                {editingUser ? t.users.editUser : t.users.addUser}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.users.name}</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  required
                  data-testid="user-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.users.email}</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  required
                  data-testid="user-email-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.users.phone}</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input-field"
                  required
                  data-testid="user-phone-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  {t.users.password} {editingUser && <span className="text-text-muted">(leave empty to keep)</span>}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="input-field"
                  required={!editingUser}
                  data-testid="user-password-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">{t.users.role}</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="input-field"
                  data-testid="user-role-select"
                >
                  <option value="manager">{t.users.manager}</option>
                  <option value="admin">{t.users.admin}</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="btn-outline flex-1">
                  {t.common.cancel}
                </button>
                <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="save-user-button">
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
