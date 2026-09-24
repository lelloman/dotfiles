import { execFileSync } from "node:child_process"

const attentionEvents = new Set([
  "permission.asked",
  "question.asked",
  "session.error",
  "session.idle",
])

function xdotool(...args) {
  try {
    return execFileSync("xdotool", args, {
      encoding: "utf8",
      timeout: 1000,
      stdio: ["ignore", "pipe", "ignore"],
    }).trim()
  } catch {
    return null
  }
}

export const I3UrgencyPlugin = async () => {
  const window = process.env.OPENCODE_I3_WINDOWID
  if (!process.env.DISPLAY || !/^\d+$/.test(window ?? "")) return {}

  return {
    event: async ({ event }) => {
      if (!attentionEvents.has(event.type)) return
      if (xdotool("getactivewindow") === window) return
      xdotool("set_window", "--urgency", "1", window)
    },
  }
}
