import React from 'react';
import Link from 'next/link';
import './error-screen.css';

export interface ErrorAction {
  label: string;
  href?: string;
  onClick?: () => void;
  primary?: boolean;
}

interface ErrorScreenProps {
  code: string;
  title: string;
  message: string;
  actions: ErrorAction[];
  detail?: string;
}

/** Calendar cells that form the backdrop; a few are "missing" shifts. */
const CELLS = Array.from({ length: 28 }, (_, i) => i);
const FILLED = new Set([0, 2, 3, 6, 8, 9, 11, 14, 15, 17, 20, 22, 23, 26]);
const COLORS = ['m', 'd', 'e', 'n'];

export default function ErrorScreen({ code, title, message, actions, detail }: ErrorScreenProps) {
  return (
    <div className="es">
      <div className="es-blob es-blob-a" />
      <div className="es-blob es-blob-b" />

      <header className="es-top">
        <Link href="/landing" className="es-brand">
          <span className="es-brand-mark">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                fill="currentColor"
                d="M7 2h2v2h6V2h2v2h3a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3V2Zm12 8H5v9h14v-9ZM5 8h14V6H5v2Z"
              />
            </svg>
          </span>
          ShiftMaster AI
        </Link>
      </header>

      <main className="es-main">
        <div className="es-visual" aria-hidden="true">
          <div className="es-grid">
            {CELLS.map((i) => (
              <span
                key={i}
                className={FILLED.has(i) ? `es-cell es-chip-${COLORS[i % 4]}` : 'es-cell es-empty'}
                style={{ animationDelay: `${i * 45}ms` }}
              />
            ))}
          </div>
          <div className="es-code">{code}</div>
        </div>

        <h1 className="es-title">{title}</h1>
        <p className="es-message">{message}</p>
        {detail && <code className="es-detail">{detail}</code>}

        <div className="es-actions">
          {actions.map((action) =>
            action.href ? (
              <Link key={action.label} href={action.href} className={`es-btn ${action.primary ? 'es-btn-primary' : ''}`}>
                {action.label}
              </Link>
            ) : (
              <button key={action.label} type="button" onClick={action.onClick} className={`es-btn ${action.primary ? 'es-btn-primary' : ''}`}>
                {action.label}
              </button>
            )
          )}
        </div>
      </main>

      <footer className="es-foot">© {new Date().getFullYear()} ShiftMaster AI</footer>
    </div>
  );
}
