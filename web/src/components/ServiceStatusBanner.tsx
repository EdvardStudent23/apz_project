import { useServiceHealth } from '@/health/ServiceHealthContext';

/**
 * Sticky top-of-viewport banner that appears whenever the API monitor sees
 * consecutive service-unavailable responses (5xx / 502 / network errors).
 * Auto-dismisses as soon as a single successful call lands — no manual close.
 */
export function ServiceStatusBanner() {
  const { status, recentFailures } = useServiceHealth();
  if (status !== 'degraded') return null;

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        margin: 0,
        padding: '12px 20px',
        background: 'var(--color-warn-bg)',
        color: 'var(--color-warn)',
        borderBottom: '1px solid var(--color-warn-border)',
        fontSize: 'var(--fs-sm)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-3)',
        textAlign: 'center',
      }}
    >
      <span aria-hidden style={{ fontSize: 16 }}>🛠</span>
      <span>
        <strong>Some services are temporarily unavailable.</strong>{' '}
        We're investigating — your account and balances are safe. Operations will
        resume automatically as soon as the services come back online.
      </span>
      <span
        className="muted"
        style={{ fontSize: 'var(--fs-xs)', whiteSpace: 'nowrap' }}
        title="Consecutive failed background checks"
      >
        ({recentFailures} retries)
      </span>
    </div>
  );
}
