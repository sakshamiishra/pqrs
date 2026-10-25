import { useCallback, useEffect, useMemo, useState } from 'react'
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { sampleProfileRows } from './profileSampling.js'

const API = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
const fmt = (v, digits = 0) => v == null ? '—' : Number(v).toLocaleString('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits })
const when = (v) => v ? new Date(v).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London' }) : '—'

function Metric({ label, value, unit, note, dark }) {
  return <article className={'metric' + (dark ? ' metric-dark' : '')}><div className="metric-label">{label}</div><div className="metric-value">{value}<span>{unit}</span></div><div className="metric-note">{note}</div></article>
}
function Hover({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  return <div className="hover-card"><b>{when(label)}</b>{payload.map((p) => <div key={p.dataKey}><i style={{ background: p.color }} />{p.name}<strong>{fmt(p.value)} MW</strong></div>)}</div>
}

export default function Dashboard() {
  const [data, setData] = useState(null), [error, setError] = useState(''), [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const response = await fetch(API + '/api/overview')
      if (!response.ok) throw new Error('Backend returned ' + response.status + '. Check that the API is running.')
      setData(await response.json())
    } catch (e) { setError(e.message || 'Could not reach the analysis API.'); setData(null) }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { load() }, [load])
  const rows = data ? data.records : []
  const profile = useMemo(() => sampleProfileRows(rows), [data])
  const errorRows = useMemo(() => { const valid = rows.filter((r) => r.error_mw != null); const step = Math.max(1, Math.ceil(valid.length / 750)); return valid.filter((_, i) => i % step === 0) }, [data])
  return <main className="page">
    <header className="nav"><div className="brand"><span className="brand-icon">W</span><div>GRIDBRICKS<small>ENERGY ANALYTICS</small></div></div><div className="source-status"><i className={loading ? 'waiting' : error ? 'offline' : ''} />{loading ? 'LOADING ELEXON DATA' : error ? 'DATA UNAVAILABLE' : 'ELEXON SOURCE'}</div></header>
    <section className="hero"><div className="hero-text"><div className="eyebrow"><i />PROCUREMENT INTELLIGENCE <span>/ WIND</span></div><h1>Forecasts, seen<br /><em>as they were.</em></h1><p>Understand the wind generation forecast available at decision time, and how it compared with actual output.</p><div className="hero-window"><small>ANALYSIS WINDOW</small><b>01 Jan — 31 Jan 2026</b><span>31 decision days</span></div></div><div className="wind-art" aria-hidden="true"><div className="sun"></div><div className="turbine turbine-a"><i></i><b></b><b></b><b></b></div><div className="turbine turbine-b"><i></i><b></b><b></b><b></b></div><span>GB WIND<br /><strong>DAY-AHEAD</strong><small>FORECAST INTELLIGENCE</small></span></div></section>
    <section className="period"><div><small>DECISION WINDOW</small><b>01–31 Jan 2026</b></div><div><small>DELIVERY WINDOW</small><b>02 Jan–01 Feb 2026</b></div><span>● &nbsp;HISTORICAL ANALYSIS</span></section>
    <section className="section-title"><div><div className="eyebrow dark"><i />ACCURACY SNAPSHOT</div><h2>How close were the forecasts?</h2></div><small>ALL VALUES IN MW UNLESS STATED</small></section>
    {error && <div className="notice error"><div><b>We couldn’t load the analysis.</b><p>{error}</p></div><button onClick={load}>Retry ↗</button></div>}
    {loading && <div className="notice"><span className="spinner" /> Fetching selected Elexon records…</div>}
    {!loading && !error && data && <section className="metrics">
      <Metric label="MEAN ABSOLUTE ERROR" value={fmt(data.metrics.mae_mw)} unit="MW" note="Average size of forecast miss" />
      <Metric label="ROOT MEAN SQUARED ERROR" value={fmt(data.metrics.rmse_mw)} unit="MW" note="Weights larger misses more" />
      <Metric label="FORECAST BIAS" value={fmt(data.metrics.bias_mw)} unit="MW" note={data.metrics.bias_mw == null ? 'Forecast minus actual' : data.metrics.bias_mw >= 0 ? 'Net over-forecasting' : 'Net under-forecasting'} />
      <Metric label="WEIGHTED ABSOLUTE ERROR" value={fmt(data.metrics.wape_percent, 1)} unit="%" note="Absolute error ÷ absolute actual" />
      <Metric label="DATA COVERAGE" value={fmt(data.coverage.percent, 1)} unit="%" note={fmt(data.coverage.matched_intervals) + ' of ' + fmt(data.coverage.eligible_intervals) + ' intervals'} dark />
    </section>}
    {!loading && !error && data && data.coverage.matched_intervals === 0 && <div className="notice empty"><b>No valid forecast and actual pairs were available.</b><p>Metrics remain blank when no pairs exist. Review the coverage counts below.</p></div>}
    {!loading && !error && data && <section className="charts">
      <article className="panel"><div className="panel-head"><div><div className="eyebrow dark"><i />GENERATION PROFILE</div><h3>Forecast vs actual</h3></div><small>MW</small></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={profile}><CartesianGrid stroke="#e7ece8" vertical={false} /><XAxis dataKey="delivery_time" tickFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'Europe/London' })} tickLine={false} axisLine={false} minTickGap={25} /><YAxis tickLine={false} axisLine={false} width={48} tickFormatter={(v) => Math.round(v / 1000) + 'k'} /><Tooltip content={<Hover />} /><Legend verticalAlign="top" align="right" iconType="circle" /><Line name="Actual" dataKey="actual_mw" type="monotone" stroke="#173f3a" strokeWidth={2} dot={false} /><Line name="Forecast" dataKey="forecast_mw" type="monotone" stroke="#ce914b" strokeWidth={2} dot={false} strokeDasharray="5 4" /></LineChart></ResponsiveContainer></div><div className="chart-caption"><span><i></i>Actual generation</span><span><i className="dash"></i>Selected forecast at decision cutoff</span></div></article>
      <article className="panel"><div className="panel-head"><div><div className="eyebrow dark"><i />INTERVAL ERROR</div><h3>Forecast miss over time</h3></div><small>MW</small></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={errorRows}><CartesianGrid stroke="#e7ece8" vertical={false} /><XAxis dataKey="delivery_time" tickFormatter={(v) => new Date(v).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'Europe/London' })} tickLine={false} axisLine={false} minTickGap={25} /><YAxis tickLine={false} axisLine={false} width={48} /><Tooltip content={<Hover />} /><Area name="Forecast error" dataKey="error_mw" type="monotone" stroke="#9c6633" fill="#d7a269" fillOpacity={0.2} /></AreaChart></ResponsiveContainer></div><div className="chart-caption">Forecast error = forecast minus actual. Positive means over-forecasting.</div></article>
    </section>}
    {!loading && !error && data && <section className="panel records"><div className="panel-head"><div><div className="eyebrow dark"><i />INTERVAL DETAIL</div><h3>Delivery records</h3></div><small>{fmt(rows.length)} EXPECTED INTERVALS</small></div><div className="table-scroll"><table><thead><tr><th>DELIVERY INTERVAL</th><th>ACTUAL WIND</th><th>SELECTED FORECAST</th><th>FORECAST PUBLISHED</th><th>ERROR</th></tr></thead><tbody>{rows.filter((r) => r.actual_mw != null || r.forecast_mw != null).slice(0, 240).map((r) => <tr key={r.delivery_time}><td><b>{when(r.delivery_time)}</b><small>SP {String(r.settlement_period).padStart(2, '0')}</small></td><td>{fmt(r.actual_mw)}<small>MW</small></td><td>{fmt(r.forecast_mw)}<small>MW</small></td><td>{when(r.forecast_publish_time)}</td><td className={r.error_mw > 0 ? 'positive' : r.error_mw < 0 ? 'negative' : ''}>{fmt(r.error_mw)}<small>MW</small></td></tr>)}</tbody></table></div><div className="table-note">Showing up to 240 intervals with at least one observation. Unmatched intervals are included in coverage counts.</div></section>}
    {!loading && !error && data && <section className="assumptions"><article className="assumption"><div className="assumption-icon">⌁</div><div><div className="eyebrow dark"><i />FORECAST SELECTION</div><h3>Decision-time cutoff</h3><p>{data.scope.cutoff_assumption} The latest forecast at or before this cutoff is selected for each half-hour delivery interval.</p><b className="cutoff">12:00 <small>EUROPE/LONDON · DAY BEFORE DELIVERY</small></b></div></article><article className="assumption"><div className="assumption-icon">▦</div><div><div className="eyebrow dark"><i />DATA COMPLETENESS</div><h3>Interval coverage</h3><p>{fmt(data.coverage.matched_intervals)} matched intervals out of {fmt(data.coverage.eligible_intervals)} expected half-hour intervals ({fmt(data.coverage.percent, 1)}% coverage). Coverage measures data completeness, not forecast accuracy. Exact timestamp matching pairs hourly forecasts with hour-start actuals; the :30 actual intervals have no matching hourly forecast and remain unmatched.</p><div className="coverage-list"><span>Matched pairs <b>{fmt(data.coverage.matched_intervals)}</b></span><span>Actual only <b>{fmt(data.coverage.actual_only)}</b></span><span>Forecast only <b>{fmt(data.coverage.forecast_only)}</b></span><span>Neither available <b>{fmt(data.coverage.missing_both)}</b></span><span>Invalid numeric values <b>{fmt(data.coverage.invalid_actual_values + data.coverage.invalid_forecast_values + data.coverage.invalid_error_pairs)}</b></span><span>Duplicate rows <b>{fmt(data.coverage.duplicate_actual_records + data.coverage.duplicate_forecast_publications)}</b></span></div></div></article></section>}
    <footer><b>WIND FORECAST INTELLIGENCE</b><span>Source: <a href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream" target="_blank" rel="noreferrer">Elexon BMRS</a> · FUELHH (WIND) and WINDFOR</span><span>Decision support only · Not a procurement recommendation</span></footer>
  </main>
}
