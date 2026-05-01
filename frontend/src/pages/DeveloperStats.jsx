/**
 * Developer Stats page — Per-developer analytics with trend charts.
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { fetchDeveloperStats } from '../api/client';
import RiskScoreCard from '../components/RiskScoreCard';

/* ── Pie chart colors ──────────────────────────────────────── */
const PIE_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

/* ── Custom Tooltip ────────────────────────────────────────── */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs" style={{ minWidth: 160 }}>
      <p className="font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
        {label || payload[0]?.name}
      </p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || p.fill }}>
          {p.name}: <span className="font-mono font-semibold">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </p>
      ))}
    </div>
  );
}

export default function DeveloperStats() {
  const { username } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchDeveloperStats(username);
        if (res.success && res.data && res.data.found) {
          setData(res.data);
        } else {
          setData({ found: false });
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [username]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24">
        <div className="skeleton h-32 rounded-2xl mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="skeleton h-80 rounded-2xl" />
          <div className="skeleton h-80 rounded-2xl" />
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

  if (!data || !data.found) {
    return (
      <div className="max-w-7xl mx-auto px-6 pt-24 pb-12">
        <div className="glass-card p-10 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <h2 className="text-xl font-bold mb-2">Developer not found</h2>
          <p>No reviews found for @{username}.</p>
        </div>
      </div>
    );
  }

  const d = data;
  const pieData = Object.entries(d.issue_breakdown || {}).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value,
  }));
  const trendData = (d.trend || []).map((t, i) => ({
    ...t,
    label: `PR #${t.pr_number || i + 1}`,
    date: new Date(t.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }));

  const hasTrendData = trendData && trendData.length > 0;
  const hasIssueBreakdown = pieData.reduce((acc, curr) => acc + curr.value, 0) > 0;

  return (
    <div className="max-w-7xl mx-auto px-6 pt-24 pb-12">
      {/* Breadcrumb */}
      <div className="mb-6 animate-fade-in">
        <Link to="/" className="text-xs no-underline" style={{ color: 'var(--color-text-muted)' }}>
          Dashboard
        </Link>
        <span className="text-xs mx-2" style={{ color: 'var(--color-text-muted)' }}>/</span>
        <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          Developer @{username}
        </span>
      </div>

      {/* Developer Header */}
      <div className="glass-card p-6 mb-6 animate-fade-in">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            {/* Avatar placeholder */}
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold"
              style={{
                background: 'var(--gradient-primary)',
                color: '#fff',
              }}>
              {username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                @{username}
              </h1>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                {d.total_reviews} reviews analyzed
              </p>
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-8">
            <RiskScoreCard score={d.avg_risk_score} label="Avg Risk" size="sm" />
            <div className="text-center">
              <span className="text-2xl font-bold block" style={{ color: 'var(--color-accent-blue)' }}>
                {d.total_reviews}
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Total PRs</span>
            </div>
            <div className="text-center">
              <span className="text-2xl font-bold block" style={{ color: '#ef4444' }}>
                {d.issue_breakdown?.critical || 0}
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Critical</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
        {/* Risk Score Trend */}
        <div className="glass-card p-5 animate-fade-in animate-fade-in-delay-1">
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            📈 Risk Score Per PR Over Time
          </h2>
          {!hasTrendData ? (
             <div className="flex items-center justify-center h-[260px]" style={{ color: 'var(--color-text-muted)' }}>
                No data yet
             </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip content={<ChartTooltip />} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="risk_score" name="Risk Score"
                  stroke="#ef4444" strokeWidth={2} dot={{ r: 3, fill: '#ef4444' }} />
                <Line type="monotone" dataKey="quality_score" name="Quality Score"
                  stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3, fill: '#8b5cf6' }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Issue Breakdown Pie */}
        <div className="glass-card p-5 animate-fade-in animate-fade-in-delay-2">
          <h2 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            🍩 Issue Breakdown by Severity
          </h2>
          {!hasIssueBreakdown ? (
             <div className="flex items-center justify-center h-[260px]" style={{ color: 'var(--color-text-muted)' }}>
                No data yet
             </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={95}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[entry.name.toLowerCase()] || '#64748b'} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
