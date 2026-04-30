import { Link, useLocation } from 'react-router-dom';

/**
 * Top navigation bar with gradient accent and active route highlighting.
 */
export default function Navbar() {
  const location = useLocation();

  const links = [
    { to: '/', label: 'Dashboard', icon: '📊' },
    { to: '/reviews', label: 'Reviews', icon: '📝' },
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: 'rgba(10, 14, 26, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--color-border)',
      }}>
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg"
            style={{ background: 'var(--gradient-primary)' }}>
            🤖
          </div>
          <div>
            <span className="text-base font-bold"
              style={{ color: 'var(--color-text-primary)' }}>
              CodeReview
            </span>
            <span className="text-base font-light ml-1"
              style={{ color: 'var(--color-accent-cyan)' }}>
              AI
            </span>
          </div>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium no-underline transition-all duration-200"
              style={{
                color: isActive(link.to)
                  ? 'var(--color-text-primary)'
                  : 'var(--color-text-secondary)',
                background: isActive(link.to)
                  ? 'rgba(59, 130, 246, 0.12)'
                  : 'transparent',
                border: isActive(link.to)
                  ? '1px solid rgba(59, 130, 246, 0.2)'
                  : '1px solid transparent',
              }}
            >
              <span>{link.icon}</span>
              <span>{link.label}</span>
            </Link>
          ))}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2 text-xs"
          style={{ color: 'var(--color-text-muted)' }}>
          <span className="w-2 h-2 rounded-full animate-pulse-glow"
            style={{ background: 'var(--color-success)' }} />
          <span>System Online</span>
        </div>
      </div>
    </nav>
  );
}
