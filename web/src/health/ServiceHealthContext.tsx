import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { subscribeApiHealth } from '@/api/client';

export type HealthStatus = 'ok' | 'degraded';

interface ServiceHealthContextValue {
  status: HealthStatus;
  /** Number of consecutive "service down" failures currently in the window. */
  recentFailures: number;
  /** Timestamp (ms) of the last successful API call. */
  lastSuccessAt: number | null;
  /** Timestamp (ms) of the last failure of any kind. */
  lastFailureAt: number | null;
}

const ServiceHealthContext = createContext<ServiceHealthContextValue | null>(null);

// Threshold of consecutive failures before we consider the back end degraded.
// Two is enough to filter out a single transient blip while still reacting
// fast (within ~10s at the dashboard's 5s polling cadence).
const DEGRADED_THRESHOLD = 2;

export function ServiceHealthProvider({ children }: { children: ReactNode }) {
  const [recentFailures, setRecentFailures] = useState(0);
  const [lastSuccessAt, setLastSuccessAt] = useState<number | null>(null);
  const [lastFailureAt, setLastFailureAt] = useState<number | null>(null);
  const consecutiveRef = useRef(0);

  useEffect(() => {
    return subscribeApiHealth((event) => {
      const now = Date.now();
      if (event === 'success') {
        consecutiveRef.current = 0;
        setRecentFailures(0);
        setLastSuccessAt(now);
      } else {
        consecutiveRef.current += 1;
        setRecentFailures(consecutiveRef.current);
        setLastFailureAt(now);
      }
    });
  }, []);

  const status: HealthStatus = recentFailures >= DEGRADED_THRESHOLD ? 'degraded' : 'ok';

  const value = useMemo<ServiceHealthContextValue>(
    () => ({ status, recentFailures, lastSuccessAt, lastFailureAt }),
    [status, recentFailures, lastSuccessAt, lastFailureAt],
  );

  return (
    <ServiceHealthContext.Provider value={value}>{children}</ServiceHealthContext.Provider>
  );
}

export function useServiceHealth(): ServiceHealthContextValue {
  const ctx = useContext(ServiceHealthContext);
  if (!ctx) throw new Error('useServiceHealth must be used inside <ServiceHealthProvider>');
  return ctx;
}
