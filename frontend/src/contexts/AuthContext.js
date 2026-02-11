import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Check if running inside Telegram WebApp
const isTelegramWebApp = () => {
  return window.Telegram?.WebApp?.initData && window.Telegram.WebApp.initData.length > 0;
};

// Get Telegram WebApp instance
const getTelegramWebApp = () => {
  return window.Telegram?.WebApp;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('crm_token'));
  const [loading, setLoading] = useState(true);
  const [isTelegram, setIsTelegram] = useState(false);
  const [telegramLinkRequired, setTelegramLinkRequired] = useState(false);
  const [telegramUser, setTelegramUser] = useState(null);

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = getTelegramWebApp();
    if (tg && isTelegramWebApp()) {
      setIsTelegram(true);
      tg.ready();
      tg.expand();
      
      // Apply Telegram theme
      document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
      document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
    }
  }, []);

  // Handle authentication
  useEffect(() => {
    const initAuth = async () => {
      // If running in Telegram, try Telegram auth first
      if (isTelegramWebApp()) {
        const tg = getTelegramWebApp();
        try {
          const response = await axios.post(`${API_URL}/api/auth/telegram`, {
            initData: tg.initData
          }, { timeout: 15000 }); // 15 second timeout
          
          if (response.data.status === 'success') {
            // Telegram user is linked - auto login
            const { token: newToken, user: userData } = response.data;
            localStorage.setItem('crm_token', newToken);
            axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
            setToken(newToken);
            setUser(userData);
            setLoading(false);
            return;
          } else if (response.data.status === 'not_linked') {
            // Telegram user not linked - show link form
            setTelegramLinkRequired(true);
            setTelegramUser(response.data.telegram_user);
            setLoading(false);
            return;
          }
        } catch (error) {
          console.error('Telegram auth error:', error);
          // For Telegram users, if the backend is down, show a clear error
          if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            console.error('Backend timeout - server may be sleeping');
          }
          // Try to use cached token if available
          const cachedToken = localStorage.getItem('crm_token');
          if (cachedToken) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${cachedToken}`;
            try {
              await fetchUser();
              return;
            } catch (e) {
              // Token invalid, clear it
              localStorage.removeItem('crm_token');
            }
          }
          setLoading(false);
          return;
        }
      }
      
      // Normal token-based auth
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        await fetchUser();
      } else {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Auth error:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API_URL}/api/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem('crm_token', newToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  // Link Telegram account to existing CRM user
  const linkTelegramAccount = async (email, password) => {
    const tg = getTelegramWebApp();
    if (!tg) throw new Error('Not in Telegram');
    
    const response = await axios.post(`${API_URL}/api/auth/telegram/link`, {
      email,
      password,
      initData: tg.initData
    });
    
    if (response.data.status === 'success') {
      const { token: newToken, user: userData } = response.data;
      localStorage.setItem('crm_token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      setToken(newToken);
      setUser(userData);
      setTelegramLinkRequired(false);
      setTelegramUser(null);
      return userData;
    }
    
    throw new Error(response.data.message || 'Link failed');
  };

  const logout = useCallback(() => {
    localStorage.removeItem('crm_token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    
    // If in Telegram, close the mini app
    if (isTelegram) {
      const tg = getTelegramWebApp();
      if (tg) {
        tg.close();
      }
    }
  }, [isTelegram]);

  const updateUser = (userData) => {
    setUser(userData);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      loading, 
      login, 
      logout, 
      updateUser, 
      isAdmin: user?.role === 'admin',
      // Telegram specific
      isTelegram,
      telegramLinkRequired,
      telegramUser,
      linkTelegramAccount,
      telegramWebApp: getTelegramWebApp()
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
