/**
 * Displays a risk score with a circular gauge and color coding.
 * Colors: 0-25 green, 25-50 yellow, 50-75 orange, 75-100 red.
 */
export default function RiskScoreCard({ score = 0, label = 'Risk Score', size = 'md' }) {
  const numScore = Number(score) || 0;
  const clampedScore = Math.max(0, Math.min(100, numScore));

  // Color based on score
  let color, bgColor, glowColor;
  if (clampedScore >= 75) {
    color = '#ef4444'; bgColor = 'rgba(239,68,68,0.12)'; glowColor = 'rgba(239,68,68,0.2)';
  } else if (clampedScore >= 50) {
    color = '#f97316'; bgColor = 'rgba(249,115,22,0.12)'; glowColor = 'rgba(249,115,22,0.2)';
  } else if (clampedScore >= 25) {
    color = '#eab308'; bgColor = 'rgba(234,179,8,0.12)'; glowColor = 'rgba(234,179,8,0.2)';
  } else {
    color = '#22c55e'; bgColor = 'rgba(34,197,94,0.12)'; glowColor = 'rgba(34,197,94,0.2)';
  }

  // SVG circle params
  const sizeMap = { sm: 80, md: 120, lg: 160 };
  const px = sizeMap[size] || 120;
  const strokeWidth = size === 'sm' ? 4 : 6;
  const radius = (px - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (clampedScore / 100) * circumference;
  const fontSize = size === 'sm' ? '1.2rem' : size === 'lg' ? '2.2rem' : '1.75rem';

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ width: px, height: px, position: 'relative' }}>
        <svg width={px} height={px} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={px / 2} cy={px / 2} r={radius}
            stroke="var(--color-border)"
            strokeWidth={strokeWidth}
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx={px / 2} cy={px / 2} r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            style={{
              transition: 'stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: `drop-shadow(0 0 8px ${glowColor})`,
            }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-bold" style={{ fontSize, color }}>
            {clampedScore}
          </span>
          {size !== 'sm' && (
            <span className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
              / 100
            </span>
          )}
        </div>
      </div>
      {label && (
        <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          {label}
        </span>
      )}
    </div>
  );
}
