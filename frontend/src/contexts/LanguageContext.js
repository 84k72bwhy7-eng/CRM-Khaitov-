import React, { createContext, useContext, useState, useEffect } from 'react';
import uzLocale from '../locales/uz.json';
import ruLocale from '../locales/ru.json';

const LanguageContext = createContext(null);

const locales = {
  uz: uzLocale,
  ru: ruLocale
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('crm_language') || 'uz';
  });

  const [t, setT] = useState(locales[language]);

  useEffect(() => {
    localStorage.setItem('crm_language', language);
    setT(locales[language]);
    document.documentElement.lang = language;
  }, [language]);

  const switchLanguage = (lang) => {
    if (locales[lang]) {
      setLanguage(lang);
    }
  };

  const translate = (key) => {
    const keys = key.split('.');
    let value = t;
    for (const k of keys) {
      value = value?.[k];
    }
    return value || key;
  };

  return (
    <LanguageContext.Provider value={{ language, switchLanguage, t, translate }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
