import React, { useEffect, useState, useCallback } from 'react'
import { api } from './api'
import HealthPulse from './components/HealthPulse'
import MetricCard from './components/MetricCard'
import AlertsPanel from './components/AlertsPanel'
import FailingChecksTable from './components/FailingChecksTable'

function statusColorFor(score) {
  if (score >= 0.95) return { color: 'var(--good)', bg: 'var(--good-dim)', label: 'Healthy' }
  if (score >= 0.8) return { color: 'var(--warn)', bg: 'var(--warn-dim)', label: 'Needs attention' }
  return { color: 'var(--critical)', bg: 'var(--critical-dim)', label: 'Critical' }
}

export default function App() {
  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [failingChecks, setFailingChecks] = useState([])
  const [trendByMetric, setTrendByMetric] = useState({})
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  const loadAll = useCallback(async () => {
    try {
      setError(null)
      const [summaryRes, alertsRes, failingRes] = await Promise.all([
        api.healthSummary(),
        api.listAlerts(false),
        api.failingChecks(),
      ])
      setSummary(summaryRes)
      setAlerts(alertsRes.alerts)
      setFailingChecks(failingRes.failing_checks)

      const metrics = Object.keys(summaryRes.metric_breakdown || {})
      const trends = {}
      await Promise.all(
        metrics.map(async (m) => {
          const res = await api.getTrend(m, 20)
          trends[m] = res.results.map((r) => ({ score: r.score }))
        })
      )
      setTrendByMetric(trends)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  async function handleRunChecks() {
    setRunning(true)
    try {
      await api.runChecks()
      await loadAll()
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  async function handleResolve(alertId) {
    await api.resolveAlert(alertId)
    setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId))
  }

  if (loading) {
    return (
      <div className="loading-shimmer">
        Connecting to monitoring backend…
      </div>
    )
  }

  const status = summary ? statusColorFor(summary.health_score) : statusColorFor(0)

  return (
    <div>
      <div className="header">
        <div>
          <p className="header-eyebrow">Data Quality Monitor</p>
          <h1 className="header-title">
            {summary ? summary.dataset.replace('_', ' ') : 'No dataset yet'}
          </h1>
          {summary && (
            <p className="header-meta">
              {summary.row_count.toLocaleString()} rows · last run{' '}
              {new Date(summary.last_run).toLocaleString()}
            </p>
          )}
        </div>
        <button className="run-button" onClick={handleRunChecks} disabled={running}>
          {running ? 'Running checks…' : 'Run checks now'}
        </button>
      </div>

      {error && (
        <div className="error-banner">
          {error === 'No check runs found yet. POST /api/checks/run first.'
            ? 'No checks have run yet. Click "Run checks now" to get started.'
            : `Couldn't reach the backend: ${error}`}
        </div>
      )}

      {summary && (
        <>
          <div className="pulse-panel">
            <div className="pulse-score-block">
              <span className="pulse-label">Overall health score</span>
              <span className="pulse-score" style={{ color: status.color }}>
                {(summary.health_score * 100).toFixed(1)}%
              </span>
              <span
                className="pulse-status-chip"
                style={{ background: status.bg, color: status.color }}
              >
                <span
                  className="pulse-status-dot"
                  style={{ background: status.color }}
                />
                {status.label} · {summary.checks_failed} of {summary.checks_run} checks failing
              </span>
            </div>
            <HealthPulse score={summary.health_score} statusColor={status.color} />
          </div>

          <div className="metrics-grid">
            {Object.entries(summary.metric_breakdown).map(([metric, score]) => (
              <MetricCard
                key={metric}
                metric={metric}
                score={score}
                checksCount={failingChecks.filter((c) => c.metric === metric).length || 1}
                trendData={trendByMetric[metric]}
              />
            ))}
          </div>

          <div className="split-grid">
            <AlertsPanel alerts={alerts} onResolve={handleResolve} />
            <FailingChecksTable checks={failingChecks} />
          </div>
        </>
      )}
    </div>
  )
}
