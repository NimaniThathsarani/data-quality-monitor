import React, { useMemo } from 'react'

/**
 * Renders an ECG-style waveform whose "agitation" (spike height, jaggedness)
 * and color respond to the health score. A healthy score reads as a calm,
 * shallow, minty wave; a degraded score reads as a sharp, tall, rose wave —
 * literalizing the "vital signs for your data" concept.
 */
export default function HealthPulse({ score = 1, statusColor = '#34d399' }) {
  const path = useMemo(() => buildEcgPath(score), [score])

  return (
    <div className="pulse-wave-wrap">
      <svg viewBox="0 0 600 100" preserveAspectRatio="none" width="100%" height="100%">
        <defs>
          <linearGradient id="pulseFade" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={statusColor} stopOpacity="0" />
            <stop offset="15%" stopColor={statusColor} stopOpacity="1" />
            <stop offset="85%" stopColor={statusColor} stopOpacity="1" />
            <stop offset="100%" stopColor={statusColor} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={path}
          fill="none"
          stroke="url(#pulseFade)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <animate
            attributeName="stroke-dashoffset"
            from="1200"
            to="0"
            dur="3.5s"
            repeatCount="indefinite"
          />
        </path>
        <path
          d={path}
          fill="none"
          stroke={statusColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="1200"
          strokeDashoffset="1200"
          opacity="0.9"
        >
          <animate
            attributeName="stroke-dashoffset"
            from="1200"
            to="0"
            dur="3.5s"
            repeatCount="indefinite"
          />
        </path>
      </svg>
    </div>
  )
}

// Builds an SVG path that looks like an ECG trace. Lower `score` -> taller,
// sharper spikes and more of them (more "agitated" reading).
function buildEcgPath(score) {
  const width = 600
  const height = 100
  const midY = height / 2
  const agitation = 1 - Math.max(0, Math.min(1, score)) // 0 = calm, 1 = agitated
  const spikeHeight = 10 + agitation * 55
  const segment = 100
  const segments = Math.floor(width / segment)

  let d = `M 0 ${midY}`
  for (let i = 0; i < segments; i++) {
    const x0 = i * segment
    // flat baseline lead-in
    d += ` L ${x0 + 25} ${midY}`
    // small pre-wave
    d += ` L ${x0 + 35} ${midY - spikeHeight * 0.15}`
    // sharp down-up spike (QRS-like)
    d += ` L ${x0 + 45} ${midY + spikeHeight * 0.3}`
    d += ` L ${x0 + 52} ${midY - spikeHeight}`
    d += ` L ${x0 + 59} ${midY + spikeHeight * 0.5}`
    d += ` L ${x0 + 68} ${midY}`
    // small after-wave, taller/rougher when unhealthy
    d += ` L ${x0 + 80} ${midY - spikeHeight * 0.2 - agitation * 8}`
    d += ` L ${x0 + 90} ${midY}`
  }
  d += ` L ${width} ${midY}`
  return d
}
