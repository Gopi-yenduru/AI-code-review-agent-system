/**
 * Review Detail page — Shows full results from all 3 AI agents for a single PR.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchReviewById } from '../api/client';
import RiskScoreCard from '../components/RiskScoreCard';
import AgentResultPanel from '../components/AgentResultPanel';

export default function ReviewDetail() {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchReviewById(id);
        if (res.success && res.data) {
          setReview(res.data);
        } else {
          setError(true);
        }
      } catch {
        setError(true);
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

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24">
        <div className="glass-card p-10 text-center text-red-400">
          <h2 className="text-xl font-bold mb-2">Failed to load data</h2>
          <p>Please check if the backend API is running.</p>
          <div className="mt-6">
            <Link to="/" style={{ color: 'var(--color-accent-blue)' }}>← Back to Dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  if (!review) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24 text-center">
        <span className="text-4xl block mb-4">🔍</span>
        <h2 className="text-xl font-semibold mb-2">No reviews yet</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>Could not find review with this ID.</p>
        <div className="mt-6">
          <Link to="/" style={{ color: 'var(--color-accent-blue)' }}>← Back to Dashboard</Link>
        </div>
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
            Total Issues: <span className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{r.total_issues || 0}</span>
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
