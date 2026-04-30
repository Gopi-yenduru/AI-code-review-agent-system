/**
 * Displays results from a single AI agent (Security, Performance, or Quality).
 * Shows header with agent icon, issue count, and the issue list.
 */
import IssueList from './IssueList';

const agentConfig = {
  security: {
    icon: '🔒',
    label: 'Security Auditor',
    accent: '#ef4444',
    accentBg: 'rgba(239,68,68,0.08)',
    borderColor: 'rgba(239,68,68,0.2)',
  },
  performance: {
    icon: '⚡',
    label: 'Performance Analyst',
    accent: '#f97316',
    accentBg: 'rgba(249,115,22,0.08)',
    borderColor: 'rgba(249,115,22,0.2)',
  },
  quality: {
    icon: '📋',
    label: 'Code Quality Judge',
    accent: '#8b5cf6',
    accentBg: 'rgba(139,92,246,0.08)',
    borderColor: 'rgba(139,92,246,0.2)',
  },
};

export default function AgentResultPanel({
  agentType = 'security',
  issues = [],
  score = null,
  highlights = [],
}) {
  const config = agentConfig[agentType] || agentConfig.security;
  const issueCount = issues.length;

  return (
    <div className="glass-card flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between"
        style={{
          borderBottom: `1px solid ${config.borderColor}`,
          background: config.accentBg,
          borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
        }}>
        <div className="flex items-center gap-3">
          <span className="text-xl">{config.icon}</span>
          <span className="text-sm font-semibold" style={{ color: config.accent }}>
            {config.label}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {score !== null && (
            <span className="text-xs font-mono px-2 py-1 rounded-md"
              style={{
                background: 'rgba(139,92,246,0.15)',
                color: '#c4b5fd',
                border: '1px solid rgba(139,92,246,0.3)',
              }}>
              Score: {score}/100
            </span>
          )}
          <span className="text-xs px-2 py-1 rounded-md font-mono"
            style={{
              background: issueCount > 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
              color: issueCount > 0 ? '#fca5a5' : '#86efac',
              border: `1px solid ${issueCount > 0 ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)'}`,
            }}>
            {issueCount} issue{issueCount !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Highlights (Quality agent) */}
      {highlights.length > 0 && (
        <div className="px-5 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <span className="text-xs font-semibold block mb-2"
            style={{ color: 'var(--color-accent-cyan)' }}>
            ✨ Highlights
          </span>
          <ul className="flex flex-col gap-1">
            {highlights.map((h, i) => (
              <li key={i} className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                • {h}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues */}
      <div className="p-4 flex-1 overflow-y-auto" style={{ maxHeight: '500px' }}>
        <IssueList
          issues={issues}
          emptyMessage={`No ${agentType} issues detected`}
        />
      </div>
    </div>
  );
}
