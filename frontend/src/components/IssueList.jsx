/**
 * Renders a list of issues with severity badges and expandable suggestions.
 */
import { useState } from 'react';

const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

function SeverityBadge({ severity }) {
  const s = (severity || 'medium').toLowerCase();
  return <span className={`badge badge-${s}`}>{s}</span>;
}

export default function IssueList({ issues = [], emptyMessage = 'No issues found' }) {
  const [expandedId, setExpandedId] = useState(null);

  const sorted = [...issues].sort(
    (a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
  );

  if (sorted.length === 0) {
    return (
      <div className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
        <span className="text-2xl block mb-2">✅</span>
        <span className="text-sm">{emptyMessage}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {sorted.map((issue, idx) => {
        const key = issue.id || `issue-${idx}`;
        const isExpanded = expandedId === key;

        return (
          <div
            key={key}
            className="rounded-lg cursor-pointer transition-all duration-200"
            style={{
              background: isExpanded ? 'rgba(59,130,246,0.06)' : 'rgba(255,255,255,0.02)',
              border: `1px solid ${isExpanded ? 'var(--color-border-light)' : 'var(--color-border)'}`,
              padding: '12px 16px',
            }}
            onClick={() => setExpandedId(isExpanded ? null : key)}
          >
            <div className="flex items-start gap-3">
              <SeverityBadge severity={issue.severity} />
              <div className="flex-1 min-w-0">
                <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-primary)' }}>
                  {issue.description}
                </p>
                <div className="flex items-center gap-4 mt-1.5">
                  {issue.line_number && (
                    <span className="text-xs font-mono" style={{ color: 'var(--color-text-muted)' }}>
                      Line {issue.line_number}
                    </span>
                  )}
                  {issue.file_path && (
                    <span className="text-xs font-mono truncate" style={{ color: 'var(--color-text-muted)' }}>
                      {issue.file_path}
                    </span>
                  )}
                </div>
              </div>
              <span className="text-xs mt-1 transition-transform duration-200"
                style={{
                  color: 'var(--color-text-muted)',
                  transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)',
                }}>
                ▼
              </span>
            </div>

            {/* Suggestion (expandable) */}
            {isExpanded && issue.suggestion && (
              <div className="mt-3 ml-11 p-3 rounded-md text-sm animate-fade-in"
                style={{
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid rgba(59, 130, 246, 0.15)',
                  color: 'var(--color-text-secondary)',
                }}>
                <span className="font-semibold" style={{ color: 'var(--color-accent-cyan)' }}>
                  💡 Suggestion:
                </span>{' '}
                {issue.suggestion}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
