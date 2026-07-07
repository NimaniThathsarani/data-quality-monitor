import React from 'react'

const SEVERITY_STYLES = {
  critical: { bg: 'var(--critical-dim)', color: 'var(--critical)', label: 'Critical' },
  warning: { bg: 'var(--warn-dim)', color: 'var(--warn)', label: 'Warning' },
  info: { bg: 'var(--accent-dim)', color: 'var(--accent)', label: 'Info' },
}

function timeAgo(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function AlertsPanel({ alerts, onResolve }) {
  return (
    <div className="panel">
      <h3 className="panel-title">Active alerts</h3>
      <p className="panel-subtitle">Checks that failed their quality threshold</p>

      {alerts.length === 0 ? (
        <div className="empty-state">No active alerts — all checks are within threshold.</div>
      ) : (
        <div>
          {alerts.map((alert) => {
            const sev = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.info
            return (
              <div className="alert-row" key={alert.alert_id}>
                <span
                  className="alert-sev-chip"
                  style={{ background: sev.bg, color: sev.color }}
                >
                  {sev.label}
                </span>
                <div style={{ flex: 1 }}>
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-meta">
                    {alert.dataset} · {timeAgo(alert.timestamp)}
                  </div>
                </div>
                {onResolve && (
                  <button
                    onClick={() => onResolve(alert.alert_id)}
                    style={{
                      background: 'transparent',
                      border: '1px solid var(--border)',
                      color: 'var(--text-muted)',
                      borderRadius: 6,
                      padding: '4px 10px',
                      fontSize: 11,
                      fontFamily: 'var(--font-mono)',
                      cursor: 'pointer',
                      height: 'fit-content',
                    }}
                  >
                    Resolve
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
