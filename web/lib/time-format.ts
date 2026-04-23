/** Convert "HH:MM" 24h to "H:MM AM/PM" (handles hour 24 from API as after midnight) */
export function formatHhmm12h(hhmm: string): string {
  const [hRaw, m] = hhmm.split(":").map(Number)
  const h = hRaw % 24
  const period = h < 12 ? "AM" : "PM"
  const hour = h % 12 === 0 ? 12 : h % 12
  return `${hour}:${String(m).padStart(2, "0")} ${period}`
}
