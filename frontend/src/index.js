import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
// Note: StrictMode removed temporarily to fix data loading race condition
root.render(
  <App />
);
