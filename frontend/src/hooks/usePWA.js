import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Hook to detect if running as installed PWA
export const useIsPWA = () => {
  const [isPWA, setIsPWA] = useState(false);
  
  useEffect(() => {
    // Check if running in standalone mode (installed PWA)
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const isIOSPWA = window.navigator.standalone === true;
    setIsPWA(isStandalone || isIOSPWA);
  }, []);
  
  return isPWA;
};

// Hook to handle "Add to Home Screen" prompt
export const useAddToHomeScreen = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [canInstall, setCanInstall] = useState(false);
  const isPWA = useIsPWA();
  const { isTelegram } = useAuth();
  
  useEffect(() => {
    // Don't show install prompt if already installed or in Telegram
    if (isPWA || isTelegram) {
      setCanInstall(false);
      return;
    }
    
    const handleBeforeInstallPrompt = (e) => {
      // Prevent Chrome from automatically showing the prompt
      e.preventDefault();
      // Stash the event so it can be triggered later
      setDeferredPrompt(e);
      setCanInstall(true);
    };
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, [isPWA, isTelegram]);
  
  const promptInstall = async () => {
    if (!deferredPrompt) return false;
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    
    // Clear the deferred prompt
    setDeferredPrompt(null);
    setCanInstall(false);
    
    return outcome === 'accepted';
  };
  
  return { canInstall, promptInstall };
};

// Component to initialize PWA features
export const PWAInitializer = ({ children }) => {
  const { isTelegram } = useAuth();
  
  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator && !isTelegram) {
      navigator.serviceWorker.register('/service-worker.js')
        .then((registration) => {
          console.log('SW registered:', registration.scope);
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker?.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New content available, show update notification
                console.log('New content available, please refresh');
              }
            });
          });
        })
        .catch((error) => {
          console.log('SW registration failed:', error);
        });
    }
    
    // Handle app installed event
    window.addEventListener('appinstalled', () => {
      console.log('PWA was installed');
      // Clear the deferredPrompt
      setDeferredPrompt(null);
    });
  }, [isTelegram]);
  
  return children;
};

// Telegram-specific fullscreen helper
export const useTelegramFullscreen = () => {
  const { telegramWebApp, isTelegram } = useAuth();
  
  const requestFullscreen = () => {
    if (isTelegram && telegramWebApp) {
      telegramWebApp.expand();
      if (telegramWebApp.requestFullscreen) {
        telegramWebApp.requestFullscreen();
      }
    }
  };
  
  const exitFullscreen = () => {
    if (isTelegram && telegramWebApp && telegramWebApp.exitFullscreen) {
      telegramWebApp.exitFullscreen();
    }
  };
  
  const isFullscreen = isTelegram && telegramWebApp?.isFullscreen;
  
  return { requestFullscreen, exitFullscreen, isFullscreen };
};

export default PWAInitializer;
