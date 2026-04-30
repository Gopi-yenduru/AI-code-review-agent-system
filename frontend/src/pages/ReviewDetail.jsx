/**
 * Review Detail page — Shows full results from all 3 AI agents for a single PR.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchReviewById } from '../api/client';
import RiskScoreCard from '../components/RiskScoreCard';
import AgentResultPanel from '../components/AgentResultPanel';

/* ── MOCK DATA ─────────────────────────────────────────────── */
const MOCK_REVIEW = {
  id: 'demo-1',
  pr_url: 'https://github.com/acme/backend-api/pull/142',
  repo_name: 'acme/backend-api',
  pr_number: 142,
  pr_title: 'Add user authentication middleware',
  author: 'alice',
  overall_risk_score: 62,
  quality_score: 71,
  quality_highlights: [
    'Good separation of concerns between auth middleware and route handlers',
    'Consistent error response format across endpoints',
  ],
  status: 'completed',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  agents: {
    security: {
      count: 3,
      issues: [
        { id: 's1', severity: 'critical', description: 'JWT secret is hardcoded as "mysecret123" in the auth middleware', line_number: 15, file_path: 'middleware/auth.py', suggestion: 'Move the JWT secret to environment variables: jwt_secret = os.environ["JWT_SECRET"]' },
        { id: 's2', severity: 'high', description: 'No rate limiting on the login endpoint — vulnerable to brute force attacks', line_number: 42, file_path: 'routes/auth.py', suggestion: 'Add rate limiting using slowapi or a custom middleware: @limiter.limit("5/minute")' },
        { id: 's3', severity: 'medium', description: 'Password is logged in debug mode', line_number: 28, file_path: 'routes/auth.py', suggestion: 'Remove password from log statements or mask sensitive fields' },
      ],
    },
    performance: {
      count: 2,
      issues: [
        { id: 'p1', severity: 'high', description: 'User lookup queries the database on every request without caching', line_number: 20, file_path: 'middleware/auth.py', suggestion: 'Cache user lookups with a short TTL: @cache(ttl=300)' },
        { id: 'p2', severity: 'medium', description: 'Token validation uses synchronous cryptography in async handler', line_number: 18, file_path: 'middleware/auth.py', suggestion: 'Use run_in_threadpool() for CPU-bound crypto operations' },
      ],
    },
    quality: {
      count: 2,
      score: 71,
      highlights: [
        'Good separation of concerns between auth middleware and route handlers',
        'Consistent error response format across endpoints',
      ],
      issues: [
        { id: 'q1', severity: 'medium', description: 'Function authenticate_user() has 45 lines — consider splitting into smaller functions', line_number: 10, file_path: 'middleware/auth.py', suggestion: 'Extract token extraction, validation, and user lookup into separate functions' },
        { id: 'q2', severity: 'low', description: 'Missing type hints on function parameters', line_number: 10, file_path: 'middleware/auth.py', suggestion: 'Add type annotations: def authenticate_user(request: Request) -> User:' },
      ],
    },
  },
  total_issues: 7,
};

export default function ReviewDetail() {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchReviewById(id);
        if (res.success) {
          setReview(res.data);
        } else {
          setReview(MOCK_REVIEW);
        }
      } catch {
        setReview(MOCK_REVIEW);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24">
        <div className="skeleton h-32 rounded-2xl mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map(i => <div key={i} className="skeleton h-96 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  if (!review) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24 text-center">
        <span className="text-4xl block mb-4">🔍</span>
        <h2 className="text-xl font-semibold mb-2">Review Not Found</h2>
        <Link to="/" style={{ color: 'var(--color-accent-blue)' }}>← Back to Dashboard</Link>
      </div>
    );
  }

  const r = review;
  const agents = r.agents || {};

  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-12">
      {/* Breadcrumb */}
      <div className="mb-6 animate-fade-in">
        <Link to="/" className="text-xs no-underline" style={{ color: 'var(--color-text-muted)' }}>
          Dashboard
        </Link>
        <span className="text-xs mx-2" style={{ color: 'var(--color-text-muted)' }}>/</span>
        <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          Review #{r.pr_number}
        </span>
      </div>

      {/* PR Header Card */}
      <div className="glass-card p-6 mb-6 animate-fade-in">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs px-2 py-1 rounded-md font-mono"
                style={{
                  background: r.status === 'completed' ? 'rgba(34,197,94,0.12)' : 'rgba(234,179,8,0.12)',
                  color: r.status === 'completed' ? '#86efac' : '#fde047',
                  border: `1px solid ${r.status === 'completed' ? 'rgba(34,197,94,0.3)' : 'rgba(234,179,8,0.3)'}`,
                }}>
                {r.status}
              </span>
              <span className="text-xs font-mono" style={{ color: 'var(--color-text-muted)' }}>
                {r.repo_name}
              </span>
            </div>
            <h1 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {r.pr_title}
            </h1>
            <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--color-text-muted)' }}>
              <span>by <Link to={`/developer/${r.author}`} className="no-underline" style={{ color: 'var(--color-accent-blue)' }}>@{r.author}</Link></span>
              <span>•</span>
              <span>PR #{r.pr_number}</span>
              <span>•</span>
              <span>{new Date(r.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
              {r.pr_url && (
                <>
                  <span>•</span>
                  <a href={r.pr_url} target="_blank" rel="noopener noreferrer"
                    className="no-underline" style={{ color: 'var(--color-accent-cyan)' }}>
                    View on GitHub ↗
                  </a>
                </>
              )}
            </div>
          </div>

          {/* Risk + Quality Scores */}
          <div className="flex items-center gap-6">
            <RiskScoreCard score={r.overall_risk_score} label="Risk Score" size="md" />
            {r.quality_score !== null && (
              <RiskScoreCard
                score={100 - (r.quality_score || 0)}
                label={`Quality: ${r.quality_score}/100`}
                size="sm"
              />
            )}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex items-center gap-6 mt-5 pt-4"
          style={{ borderTop: '1px solid var(--color-border)' }}>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Total Issues: <span className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{r.total_issues}</span>
          </span>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Security: <span className="font-semibold" style={{ color: '#ef4444' }}>{agents.security?.count || 0}</span>
          </span>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Performance: <span className="font-semibold" style={{ color: '#f97316' }}>{agents.performance?.count || 0}</span>
          </span>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Quality: <span className="font-semibold" style={{ color: '#8b5cf6' }}>{agents.quality?.count || 0}</span>
          </span>
        </div>
      </div>

      {/* Three Agent Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="animate-fade-in animate-fade-in-delay-1">
          <AgentResultPanel
            agentType="security"
            issues={agents.security?.issues || []}
          />
        </div>
        <div className="animate-fade-in animate-fade-in-delay-2">
          <AgentResultPanel
            agentType="performance"
            issues={agents.performance?.issues || []}
          />
        </div>
        <div className="animate-fade-in animate-fade-in-delay-3">
          <AgentResultPanel
            agentType="quality"
            issues={agents.quality?.issues || []}
            score={agents.quality?.score}
            highlights={agents.quality?.highlights || r.quality_highlights || []}
          />
        </div>
      </div>
    </div>
  );
}
