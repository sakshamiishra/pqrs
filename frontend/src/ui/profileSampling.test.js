import test from 'node:test'
import assert from 'node:assert/strict'
import { sampleProfileRows } from './profileSampling.js'

test('profile sampling retains representative :00 and :30 actuals without adding forecast values', () => {
  const rows = Array.from({ length: 1488 }, (_, index) => {
    const delivery_time = new Date(Date.UTC(2026, 0, 2, 0, index * 30)).toISOString()
    const isHourStart = new Date(delivery_time).getUTCMinutes() === 0
    return {
      delivery_time,
      actual_mw: index,
      forecast_mw: isHourStart ? index + 1 : null,
    }
  })

  const sampled = sampleProfileRows(rows)
  const minutes = new Set(sampled.map((row) => new Date(row.delivery_time).getUTCMinutes()))

  assert.ok(sampled.length <= 750)
  assert.ok(minutes.has(0))
  assert.ok(minutes.has(30))
  assert.ok(sampled.some((row) => row.actual_mw != null && row.forecast_mw == null && new Date(row.delivery_time).getUTCMinutes() === 30))
  assert.equal(sampled.filter((row) => row.forecast_mw != null).length, sampled.filter((row) => new Date(row.delivery_time).getUTCMinutes() === 0).length)
})
