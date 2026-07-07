import React from 'react'

export default function FailingChecksTable({ checks }) {
  return (
    <div className="panel">
      <h3 className="panel-title">Failing checks</h3>
      <p className="panel-subtitle">Detail from the most recent run</p>

      {checks.length === 0 ? (
        <div className="empty-state">Every check passed on the latest run.</div>
      ) : (
        <table className="checks-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Column</th>
              <th>Score</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((c, i) => (
              <tr key={i}>
                <td className="col-metric">{c.metric}</td>
                <td>{c.column}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>
                  {(c.score * 100).toFixed(1)}%
                </td>
                <td className="col-detail">{c.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
