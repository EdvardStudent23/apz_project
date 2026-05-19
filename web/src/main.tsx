import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './styles/tokens.css';
import './styles/globals.css';
import { AuthProvider } from './auth/AuthContext';
import { ThemeProvider } from './theme/ThemeContext';
import { ServiceHealthProvider } from './health/ServiceHealthContext';
import { ServiceStatusBanner } from './components/ServiceStatusBanner';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <ServiceHealthProvider>
        <BrowserRouter>
          <AuthProvider>
            <ServiceStatusBanner />
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ServiceHealthProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
