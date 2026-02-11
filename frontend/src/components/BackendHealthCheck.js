import React, { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Backend health check states
const STATUS = {
  CHECKING: 'checking',
  READY: 'ready',
  WAKING: 'waking',
  ERROR: 'error'
};

const BackendHealthCheck = ({ children }) => {
  const [status, setStatus] = useState(STATUS.CHECKING);
  const [attempts, setAttempts] = useState(0);
  const [message, setMessage] = useState('');
  
  const maxAttempts = 10; // Maximum retry attempts
  const retryDelay = 2000; // 2 seconds between retries
  const initialDelay = 500; // Initial delay for first check

  const checkBackendHealth = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout
      
      const response = await fetch(`${API_URL}/api/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json'
        }
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          setStatus(STATUS.READY);
          return true;
        }
      }
      return false;
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Health check timed out');
      } else {
        console.log('Health check failed:', error.message);
      }
      return false;
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    let timeoutId = null;
    
    const performHealthCheck = async () => {
      if (!mounted) return;
      
      setAttempts(prev => prev + 1);
      
      if (attempts === 0) {
        setMessage('Ulanmoqda...');
      } else if (attempts < 3) {
        setMessage('Server bilan bog\'lanmoqda...');
        setStatus(STATUS.WAKING);
      } else {
        setMessage(`Serverga ulanish... (${attempts}/${maxAttempts})`);
      }
      
      const isHealthy = await checkBackendHealth();
      
      if (!mounted) return;
      
      if (isHealthy) {
        setStatus(STATUS.READY);
      } else if (attempts < maxAttempts) {
        // Retry with delay
        timeoutId = setTimeout(() => {
          if (mounted) {
            performHealthCheck();
          }
        }, retryDelay);
      } else {
        setStatus(STATUS.ERROR);
        setMessage('Serverga ulanib bo\'lmadi. Sahifani yangilang.');
      }
    };
    
    // Start health check after initial delay
    timeoutId = setTimeout(performHealthCheck, initialDelay);
    
    return () => {
      mounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [attempts, checkBackendHealth]);

  // Retry handler for error state
  const handleRetry = () => {
    setAttempts(0);
    setStatus(STATUS.CHECKING);
  };

  // Show loading screen while checking/waking
  if (status !== STATUS.READY) {
    return (
      <div className="min-h-screen bg-secondary flex flex-col items-center justify-center p-6" data-testid="backend-health-check">
        {/* Logo */}
        <div className="mb-8">
          <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center shadow-lg">
            <span className="text-3xl font-bold text-secondary">SC</span>
          </div>
        </div>
        
        {/* App Name */}
        <h1 className="text-2xl font-bold text-white mb-2">
          <span className="text-primary">School</span>CRM
        </h1>
        
        {/* Status */}
        <div className="mt-8 flex flex-col items-center">
          {status === STATUS.ERROR ? (
            <>
              {/* Error Icon */}
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-white/60 text-center mb-4">{message}</p>
              <button
                onClick={handleRetry}
                className="px-6 py-3 bg-primary text-secondary font-semibold rounded-lg active:scale-95 transition-transform"
              >
                Qayta urinish
              </button>
            </>
          ) : (
            <>
              {/* Loading Spinner */}
              <div className="relative w-12 h-12 mb-4">
                <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>
              <p className="text-white/60 text-center">{message}</p>
              
              {/* Progress dots for waking state */}
              {status === STATUS.WAKING && (
                <div className="flex gap-1 mt-4">
                  {[...Array(Math.min(attempts, 5))].map((_, i) => (
                    <div 
                      key={i} 
                      className="w-2 h-2 rounded-full bg-primary"
                      style={{ opacity: 0.3 + (i * 0.15) }}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
        
        {/* Footer hint */}
        {status === STATUS.WAKING && attempts > 3 && (
          <p className="absolute bottom-8 text-white/40 text-sm text-center px-6">
            Server uyg'onmoqda, biroz kuting...
          </p>
        )}
      </div>
    );
  }

  // Backend is ready, render children
  return children;
};

export default BackendHealthCheck;
