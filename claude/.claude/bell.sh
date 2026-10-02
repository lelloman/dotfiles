#!/bin/sh
# Ring the terminal bell on Claude's controlling tty (sets i3 urgency hint).
p=$PPID
while [ "${p:-1}" -gt 1 ]; do
  t=$(ps -o tty= -p "$p" | tr -d ' ')
  if [ -n "$t" ] && [ "$t" != "?" ]; then
    printf '\a' > "/dev/$t"
    exit 0
  fi
  p=$(ps -o ppid= -p "$p" | tr -d ' ')
done
