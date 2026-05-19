import { useTheme } from '@/theme/ThemeContext';
import { Button } from './Button';

interface Props {
  variant?: 'ghost' | 'secondary';
}

export function ThemeToggle({ variant = 'ghost' }: Props) {
  const { resolved, toggle } = useTheme();
  const isDark = resolved === 'dark';
  return (
    <Button
      variant={variant}
      onClick={toggle}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label="Toggle theme"
      style={{ padding: '8px 10px', minWidth: 0 }}
    >
      <span aria-hidden style={{ fontSize: 16, lineHeight: 1 }}>
        {isDark ? '☀' : '☾'}
      </span>
    </Button>
  );
}
