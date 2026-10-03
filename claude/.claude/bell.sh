#!/bin/sh
# Flag Claude's terminal window as urgent, so its i3 workspace blinks.
#
# A plain BEL is not enough: GNOME Terminal doesn't set the X urgency hint on
# bell (it expects the window manager to react, which i3 doesn't), and it
# doesn't export WINDOWID either. So find the window by briefly giving it a
# unique title through Claude's controlling tty, then set the hint directly.

p=$PPID
tty=
while [ "${p:-1}" -gt 1 ]; do
  t=$(ps -o tty= -p "$p" | tr -d ' ')
  if [ -n "$t" ] && [ "$t" != "?" ]; then
    tty=/dev/$t
    break
  fi
  p=$(ps -o ppid= -p "$p" | tr -d ' ')
done
[ -n "$tty" ] || exit 0

printf '\a' > "$tty"

[ -n "$DISPLAY" ] && command -v xdotool >/dev/null 2>&1 || exit 0

marker="claude-bell-$$"
wins=
i=0
# Save the current title on the terminal's title stack, restored below.
printf '\033[22;0t' > "$tty"
while [ "$i" -lt 20 ]; do
  # Re-sent every round: Claude may overwrite the title while we poll.
  printf '\033]0;%s\033\\' "$marker" > "$tty"
  sleep 0.05
  wins=$(xdotool search --name "^$marker\$" 2>/dev/null)
  [ -n "$wins" ] && break
  i=$((i + 1))
done
printf '\033[23;0t' > "$tty"

active=$(xdotool getactivewindow 2>/dev/null)
for w in $wins; do
  [ "$w" = "$active" ] || xdotool set_window --urgency 1 "$w"
done
exit 0
