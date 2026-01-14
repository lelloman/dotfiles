# History settings
export HISTSIZE=10000
export HISTFILESIZE=20000

# Git aliases
alias gitpl="git log --pretty=format:'%C(yellow) %h %C(white)|%<(50,trunc)%s|%C(green)%<(20,trunc)%ar %Creset%C(cyan)|%ae %Creset'"

# Claude Code with alternative API endpoint
alias peglegclaude='CLAUDE_CONFIG_DIR=~/.claude-pegleg claude --settings ~/.claude-pegleg/settings.json'
