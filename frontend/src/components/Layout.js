import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
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
  CheckCircle,
  Phone,
  Bell
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout, isAdmin, isTelegram } = useAuth();
  const { t, language, switchLanguage } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Full navigation for desktop/web
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

  // Simplified bottom navigation for Telegram Mini App
  const mobileNavItems = [
    { to: '/clients', icon: Users, label: t.nav.clients },
    { to: '/payments', icon: CreditCard, label: t.nav.payments },
    { to: '/settings', icon: Settings, label: t.nav.settings }
  ];

  // Telegram Mini App layout - maximized content, bottom nav
  if (isTelegram) {
    return (
      <div className="min-h-screen bg-background flex flex-col safe-area-top" data-testid="telegram-layout">
        {/* Minimal Header - Only show on non-clients pages */}
        {location.pathname !== '/clients' && (
          <header className="bg-secondary text-white px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="p-1 -ml-1"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold">
              {location.pathname === '/payments' && t.nav.payments}
              {location.pathname === '/settings' && t.nav.settings}
              {location.pathname.startsWith('/clients/') && t.clients.clientDetails}
            </h1>
            <div className="w-6" /> {/* Spacer for centering */}
          </header>
        )}

        {/* Main Content - Maximized */}
        <main className="flex-1 overflow-auto pb-20">
          <div className="p-4">
            {children}
          </div>
        </main>

        {/* Bottom Navigation - Always visible */}
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border safe-area-bottom z-40">
          <div className="flex justify-around items-center h-16">
            {mobileNavItems.map((item) => {
              const isActive = location.pathname === item.to || 
                (item.to === '/clients' && location.pathname.startsWith('/clients'));
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                    isActive 
                      ? 'text-primary' 
                      : 'text-text-muted'
                  }`}
                  data-testid={`bottom-nav-${item.to.replace('/', '') || 'home'}`}
                >
                  <item.icon size={22} strokeWidth={isActive ? 2.5 : 2} />
                  <span className={`text-xs mt-1 ${isActive ? 'font-semibold' : ''}`}>
                    {item.label}
                  </span>
                </NavLink>
              );
            })}
          </div>
        </nav>
      </div>
    );
  }

  // Standard web layout
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
