import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

const proprietaryNotice = document.createElement('footer');
proprietaryNotice.setAttribute('data-ip-notice', 'true');
proprietaryNotice.textContent = '© 2026 Alexander J. Kivela. Proprietary portfolio software. All rights reserved.';
Object.assign(proprietaryNotice.style, { padding: '14px 18px', textAlign: 'center', fontSize: '12px', lineHeight: '1.5', opacity: '0.72', borderTop: '1px solid rgba(127,127,127,0.22)' });
document.body.appendChild(proprietaryNotice);
