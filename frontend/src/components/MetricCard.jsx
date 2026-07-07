import React from 'react'
import { ResponsiveContainer, LineChart, Line } from 'recharts'

const STATUS_COLORS = {
  good: 'var(--good)',
  warn: 'var(--warn)',
  critical: 'var(--critical)',
}

function statusFor(score) {
  if (score >= 0.95) return 'good'
  if (score >= 0.8) return 'warn'
  return 'critical'
}

export default function MetricCard({ metric, score, checksCount, trendData }) {
  const status = statusFor(score)
  const color = STATUS_COLORS[status]

  return (
    <div className="metric-card">
      <div className="metric-name">{metric}</div>
      <div className="metric-score" style={{ color }}>
        {(score * 100).toFixed(1)}%
      </div>
      <div className="metric-bar-track">
        <div
          className="metric-bar-fill"
          style={{ width: `${score * 100}%`, background: color }}
        />
      </div>
      {trendData && trendData.length > 1 && (
        <div style={{ height: 28 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <Line
                type="monotone"
                dataKey="score"
                stroke={color}
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="metric-footer">{checksCount} check{checksCount === 1 ? '' : 's'}</div>
    </div>
  )
}
