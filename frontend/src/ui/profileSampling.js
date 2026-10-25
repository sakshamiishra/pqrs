const PROFILE_MAX_POINTS = 750

export function sampleProfileRows(rows, maxPoints = PROFILE_MAX_POINTS) {
  const valid = rows.filter((row) => row.actual_mw != null || row.forecast_mw != null)
  if (valid.length <= maxPoints) return valid

  const groups = new Map()
  valid.forEach((row, index) => {
    const minute = new Date(row.delivery_time).getUTCMinutes()
    const group = groups.get(minute) || []
    group.push(index)
    groups.set(minute, group)
  })

  // Sample each timestamp cadence independently so an hourly forecast cadence
  // cannot cause every other (for example, :30 actual) record to disappear.
  const slotsPerGroup = Math.max(1, Math.floor(maxPoints / groups.size))
  const selected = new Set()
  groups.forEach((indices) => {
    const slots = Math.min(indices.length, slotsPerGroup)
    for (let slot = 0; slot < slots; slot += 1) {
      selected.add(indices[Math.floor(slot * indices.length / slots)])
    }
  })
  return valid.filter((_, index) => selected.has(index))
}
