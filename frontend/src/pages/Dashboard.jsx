/**
 * Dashboard page — Overview of recent reviews, risk trends, and stats.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts';
import { fetchOverviewStats } from '../api/client';
import RiskScoreCard from '../components/RiskScoreCard';

/* ── Severity badge inline ─────────────────────────────────── */
function RiskBadge({ score }) {
  const s = Number(score) || 0;
  let color, bg, border, label;
  if (s >= 75) {
    color = '#fca5a5'; bg = 'rgba(239,68,68,0.12)'; border = 'rgba(239,68,68,0.3)'; label = 'Critical';
  } else if (s >= 50) {
    color = '#fdba74'; bg = 'rgba(249,115,22,0.12)'; border = 'rgba(249,115,22,0.3)'; label = 'High';
  } else if (s >= 25) {
    color = '#fde047'; bg = 'rgba(234,179,8,0.12)'; border = 'rgba(234,179,8,0.3)'; label = 'Medium';
  } else {
    color = '#86efac'; bg = 'rgba(34,197,94,0.12)'; border = 'rgba(34,197,94,0.3)'; label = 'Low';
  }
  return (
    <span className="badge" style={{ color, background: bg, border: `1px solid ${border}` }}>
      {s.toFixed(0)} — {label}
    </span>
  );
}

/* ── Stat Card ─────────────────────────────────────────────── */
function StatCard({ icon, label, value, accent, delay }) {
  return (
    <div className={`glass-card p-5 animate-fade-in animate-fade-in-delay-${delay}`}>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xl w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: `${accent}15`, border: `1px solid ${accent}30` }}>
          {icon}
        </span>
        <span className="text-xs font-medium uppercase tracking-wider"
          style={{ color: 'var(--color-text-muted)' }}>
          {label}
        </span>
      </div>
      <span className="text-3xl font-bold" style={{ color: accent }}>{value}</span>
    </div>
  );
}

/* ── Custom Tooltip ────────────────────────────────────────── */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs" style={{ minWidth: 140 }}>
      <p className="font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-mono font-semibold">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </p>
      ))}
    </div>
  );
}

/* ── Dashboard Component ───────────────────────────────────── */
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchOverviewStats();
        if (res.success) {
          setStats(res.data);
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
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-28 rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="skeleton h-72 rounded-2xl" />
          <div className="skeleton h-72 rounded-2xl" />
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
        </div>
      </div>
    );
  }

  const d = stats || {};
  const barData = (d.weekly_issues || []).map(w => ({
    name: `${w.agent_type}\n${w.severity}`,
    count: w.count,
    fill: w.severity === 'critical' ? '#ef4444'
      : w.severity === 'high' ? '#f97316'
      : w.severity === 'medium' ? '#eab308'
      : '#22c55e',
  }));

  const hasTrendData = d.daily_trend && d.daily_trend.length > 0;
  const hasIssuesData = barData && barData.length > 0;
  const hasRecentReviews = d.recent_reviews && d.recent_reviews.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-12">
      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <h1 className="text-2xl font-bold mb-1"
          style={{ color: 'var(--color-text-primary)' }}>
          Dashboard
        </h1>
        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
          AI-powered code review insights at a glance
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <StatCard icon="📝" label="Total Reviews" value={d.total_reviews || 0} accent="#3b82f6" delay={1} />
        <StatCard icon="📊" label="Avg Risk Score" value={(d.avg_risk_score || 0).toFixed(1)} accent="#f97316" delay={1} />
        <StatCard icon="🚨" label="Critical Issues" value={d.total_critical_issues || 0} accent="#ef4444" delay={2} />
        <StatCard icon="✅" label="Reviews Today" value={
          (d.daily_trend || []).filter(t => t.date === new Date().toISOString().split('T')[0]).reduce((a, t) => a + t.count, 0) || 0
        } accent="#22c55e" delay={3} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* Risk Trend */}
        <div className="glass-card p-5 animate-fade-in animate-fade-in-delay-2">
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            📈 Risk Score Trend — Last 30 Days
          </h2>
          {!hasTrendData ? (
             <div className="flex items-center justify-center h-[240px]" style={{ color: 'var(--color-text-muted)' }}>
                No data yet
             </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={d.daily_trend}>
                <defs>
                  <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="avg_risk" name="Avg Risk"
                  stroke="#3b82f6" fill="url(#riskGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Issues This Week */}
        <div className="glass-card p-5 animate-fade-in animate-fade-in-delay-3">
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            📊 Issues This Week — By Type
          </h2>
          {!hasIssuesData ? (
             <div className="flex items-center justify-center h-[240px]" style={{ color: 'var(--color-text-muted)' }}>
                No data yet
             </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="Issues" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, idx) => (
                    <rect key={idx} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Reviews Table */}
      <div className="glass-card animate-fade-in animate-fade-in-delay-3">
        <div className="px-5 py-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
            🕐 Recent Reviews
          </h2>
        </div>
        <div className="overflow-x-auto">
          {!hasRecentReviews ? (
            <div className="p-10 text-center" style={{ color: 'var(--color-text-muted)' }}>
              No reviews yet. Open a Pull Request to trigger your first AI review.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  {['PR Title', 'Author', 'Repository', 'Risk Score', 'Time'].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider"
                      style={{ color: 'var(--color-text-muted)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {d.recent_reviews.map((r) => (
                  <tr key={r.review_id}
                    className="transition-colors duration-150"
                    style={{
                      borderBottom: '1px solid var(--color-border)',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.04)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <td className="px-5 py-3">
                      <Link to={`/reviews/${r.review_id}`}
                        className="font-medium no-underline hover:underline"
                        style={{ color: 'var(--color-accent-blue)' }}>
                        {r.pr_title}
                      </Link>
                      <span className="text-xs ml-2 font-mono" style={{ color: 'var(--color-text-muted)' }}>
                        #{r.pr_number}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <Link to={`/developer/${r.author}`}
                        className="no-underline"
                        style={{ color: 'var(--color-text-secondary)' }}>
                        @{r.author}
                      </Link>
                    </td>
                    <td className="px-5 py-3 font-mono text-xs"
                      style={{ color: 'var(--color-text-muted)' }}>
                      {r.repo_name}
                    </td>
                    <td className="px-5 py-3">
                      <RiskBadge score={r.risk_score} />
                    </td>
                    <td className="px-5 py-3 text-xs"
                      style={{ color: 'var(--color-text-muted)' }}>
                      {new Date(r.created_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
