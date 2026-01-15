# dotfiles

Personal dotfiles managed with [GNU Stow](https://www.gnu.org/software/stow/).

## Prerequisites

```bash
sudo apt install stow
```

## Installation

Clone the repo and stow the packages you want:

```bash
cd ~
git clone <repo-url> dotfiles
cd dotfiles
stow bash i3 pezzotticlaude  # or just the ones you need
```

## Packages

### bash

Shell configuration and aliases.

**Stows to:** `~/.bash_aliases`

**Contents:**
- History settings (10000 lines)
- Git log alias (`gitpl`)
- `pezzotticlaude` alias for Claude Code with alternative API

**Requires:** Your `~/.bashrc` must source `~/.bash_aliases`:
```bash
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
```

---

### i3

i3 window manager configuration.

**Stows to:** `~/.config/i3/`

**Contents:**
- Main i3 config
- Workspace assignments
- Workspace cycling script
- Layouts for terminal grids (2x2, side-by-side)

---

### pezzotticlaude

Claude Code configuration for alternative API endpoint (e.g., MiniMax).

**Stows to:** `~/.pezzotticlaude/`

**Contents:**
- `.claude.json.template` - theme and preferences template
- `.claude.json` - runtime state (gitignored, auto-generated)
- `settings.json.template` - config template (no secrets)
- `settings.json` - actual config with API key (gitignored)

**Setup (first time):**
```bash
cd ~/dotfiles/pezzotticlaude/.pezzotticlaude
cp settings.json.template settings.json
cp .claude.json.template .claude.json
# Edit settings.json and add your ANTHROPIC_AUTH_TOKEN
```

**Usage:**
```bash
pezzotticlaude  # runs Claude Code with alternative API
claude          # runs normal Claude Code
```

---

### scripts

Custom scripts.

**Stows to:** `~/.local/bin/`

**Contents:**
- `setupworkspaces` - i3 workspace setup script
- `disk-space-alert.sh` - disk space monitoring

---

## Adding new packages

1. Create a directory named after the package
2. Mirror the home directory structure inside it
3. Stow it: `stow <package-name>`

Example for a new `vim` package:
```
vim/
└── .vimrc
```

Then: `stow vim` creates `~/.vimrc -> ~/dotfiles/vim/.vimrc`

## Uninstalling

```bash
stow -D <package-name>  # removes symlinks
```
