# History settings
export HISTSIZE=10000
export HISTFILESIZE=20000

# Git aliases
alias gitpl="git log --pretty=format:'%C(yellow) %h %C(white)|%<(50,trunc)%s|%C(green)%<(20,trunc)%ar %Creset%C(cyan)|%ae %Creset'"

# Monitor configuration (DP-0 left, HDMI-0 right)
alias confmonitor='xrandr --output DP-0 --auto --left-of HDMI-0 --output HDMI-0 --auto'

# Claude Code with alternative API endpoint (purple background)
alias pezzotticlaude='echo -ne "\033]11;#2d1b4e\007"; CLAUDE_CONFIG_DIR=~/.pezzotticlaude claude --settings ~/.pezzotticlaude/settings.json; echo -ne "\033]11;#171421\007"'
