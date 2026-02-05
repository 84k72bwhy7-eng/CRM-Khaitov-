import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  LayoutDashboard, 
  Users, 
  CreditCard, 
  Settings, 
  LogOut, 
  UserCog,
  Menu,
  X,
  Globe,
  History,
  CheckCircle
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout, isAdmin } = useAuth();
  const { t, language, switchLanguage } = useLanguage();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: t.nav.dashboard },
    { to: '/clients', icon: Users, label: t.nav.clients },
    { to: '/sold', icon: CheckCircle, label: t.nav.soldClients },
    { to: '/payments', icon: CreditCard, label: t.nav.payments },
    ...(isAdmin ? [
      { to: '/users', icon: UserCog, label: t.nav.users },
      { to: '/activity-log', icon: History, label: t.nav.activityLog }
    ] : []),
    { to: '/settings', icon: Settings, label: t.nav.settings }
  ];

  return (
    <div className="min-h-screen bg-background flex" data-testid="main-layout">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-secondary text-white rounded-lg shadow-lg"
        data-testid="mobile-menu-button"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-secondary text-white transform transition-transform duration-200 ease-in-out lg:transform-none ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center gap-3" data-testid="app-logo">
              <div className="w-10 h-10 rounded-lg overflow-hidden bg-black flex-shrink-0">
                <img 
                  src="/images/logo.jpg" 
                  alt="SchoolCRM" 
                  className="w-full h-full object-cover"
                />
              </div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-primary">School</span>CRM
              </h1>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'active' : ''}`
                }
                data-testid={`nav-${item.to.replace('/', '') || 'dashboard'}`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* User info & logout */}
          <div className="p-4 border-t border-white/10">
            <div className="mb-4 px-4">
              <p className="text-sm text-white/60">{user?.role === 'admin' ? t.users.admin : t.users.manager}</p>
              <p className="font-medium truncate">{user?.name}</p>
            </div>
            <button
              onClick={handleLogout}
              className="sidebar-link w-full text-white/80 hover:text-white hover:bg-white/10"
              data-testid="logout-button"
            >
              <LogOut size={20} />
              <span>{t.nav.logout}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 flex flex-col min-h-screen w-full lg:w-auto">
        {/* Header */}
        <header className="bg-white border-b border-border px-4 lg:px-6 py-4 flex items-center justify-end gap-4" data-testid="header">
          {/* Language switcher */}
          <div className="flex items-center gap-2">
            <Globe size={18} className="text-text-secondary hidden sm:block" />
            <button
              onClick={() => switchLanguage('uz')}
              className={`px-2 sm:px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                language === 'uz'
                  ? 'bg-primary text-black'
                  : 'text-text-secondary hover:bg-gray-100'
              }`}
              data-testid="lang-uz-button"
            >
              UZ
            </button>
            <button
              onClick={() => switchLanguage('ru')}
              className={`px-2 sm:px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                language === 'ru'
                  ? 'bg-primary text-black'
                  : 'text-text-secondary hover:bg-gray-100'
              }`}
              data-testid="lang-ru-button"
            >
              RU
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 p-4 lg:p-8 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
