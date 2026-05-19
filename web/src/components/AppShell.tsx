import { ReactNode, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '@/auth/AuthContext';
import { initials } from '@/lib/format';
import { Button } from './Button';
import { ThemeToggle } from './ThemeToggle';

interface Props {
  children: ReactNode;
}

type NavItem = {
  to: string;
  label: string;
  icon: string;
  adminOnly?: boolean;
  tag?: string;
};

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: '◫' },
  { to: '/transfer', label: 'Send money', icon: '↗' },
  { to: '/history', label: 'Activity', icon: '☷' },
  { to: '/shop', label: 'Shop', icon: '✦' },
  { to: '/shop/mine', label: 'My listings', icon: '⛁' },
  { to: '/shop/orders', label: 'My orders', icon: '⌫' },
  { to: '/admin/moderation', label: 'Moderation', icon: '✓', adminOnly: true, tag: 'admin' },
];

export function AppShell({ children }: Props) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const visibleItems = navItems.filter((item) => !item.adminOnly || user?.is_admin);

  const handleSignOut = async () => {
    await signOut();
    navigate('/', { replace: true });
  };

  return (
    <div className="shell">
      <aside className={clsx('shell-sidebar', open && 'open')}>
        <div className="shell-brand">
          <span className="shell-brand-mark">N</span>
          <span>NanoBank</span>
        </div>
        <nav className="shell-nav">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => clsx('shell-nav-link', isActive && 'active')}
              onClick={() => setOpen(false)}
              end={item.to === '/shop'}
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
              {item.tag && <span className="shell-nav-tag">{item.tag}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="shell-main">
        <header className="shell-topbar">
          <div className="row">
            <button
              className="shell-burger"
              type="button"
              aria-label="Toggle navigation"
              onClick={() => setOpen((v) => !v)}
            >
              ☰
            </button>
          </div>
          <div className="row" style={{ gap: 'var(--space-3)' }}>
            <ThemeToggle />
            {user && (
              <Link to="/profile" className="user-chip" style={{ textDecoration: 'none', color: 'inherit' }} title="View profile">
                <span className="user-avatar">{initials(user.username)}</span>
                <span style={{ paddingRight: 6 }}>{user.username}</span>
              </Link>
            )}
            <Button variant="ghost" onClick={handleSignOut}>
              Sign out
            </Button>
          </div>
        </header>
        <main className="shell-content">{children}</main>
      </div>
    </div>
  );
}
