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
stow bash claude i3 sway waybar scripts vim pezzotticlaude  # or just the ones you need
```

## Packages

### bash

Shell configuration and aliases.

**Stows to:** `~/.bash_aliases`

**Contents:**
- History settings (10000 lines)
- Git log alias (`gitpl`)
- `codex` function using the notification bridge when the `scripts` package is installed
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

`Mod+Enter` opens a new window in the focused GNOME Terminal tab's current
directory, using the same profile. From other applications it uses the normal
`i3-sensible-terminal` launcher. This requires the `scripts` package, Python 3,
`xprop`, and `gdbus`.

**Stows to:** `~/.config/i3/`

**Contents:**
- Main i3 config
- Workspace assignments
- Workspace cycling script
- Ordered startup hook for monitor and workspace setup
- Layouts for terminal grids (2x2, side-by-side)
- GUI workspace editor and reusable, parameterized workspace templates

On login, i3 runs `~/.local/bin/i3-session-startup`, which calls `confmonitor`,
waits briefly for the monitor layout to settle, then runs `setupworkspaces`.
Startup output is written to `~/.local/state/i3-startup.log`.

Only workspace **1 (Chromium)** and **4 (Ronomepo)** are fixed at startup.
Project terminal workspaces are restored from the previous session, using their
saved project folders, workspace names, and displays. A background watcher saves
changes after about one second of inactivity, including display moves, renames,
and workspace closures. Its state is stored in
`~/.local/state/i3-workspace-config/session.json` (under `$XDG_STATE_HOME` if set).
If a display is unavailable, projects use the available secondary/primary
display. Missing project folders are skipped and reported in the startup log.
Restoration creates the template's three fresh terminals; it does not resume
running shell commands or recover terminal contents.

To migrate an existing installation without reopening its windows, run
`workspace-configurator --enable-session` once. This backs up the configuration,
records open project workspaces, removes the old fixed project list and the
workspace 2/5 application assignments, and starts the watcher. Existing project
workspaces are recognized by their old template entries, or by three GNOME
Terminal windows and a matching folder below `/home/lelloman/lelloprojects`.

Workspace setup is stored in `~/.config/i3/workspaces.json`. Open the editor
with:

```bash
configure-workspaces
```

The editor controls each workspace's output, layout, launch commands, working
directories, and i3 window matching rules. **Save and apply all** immediately
materializes the setup; `setupworkspaces` does the same from a terminal. Direct
and template-materialized workspaces are both shown in the main list. The title
and status line clearly mark unsaved changes, and **Reload from disk** restores
the currently saved configuration.

The normal workflow is intentionally tailored to this setup. **Add** creates a
workspace from a Chromium, VS Code, Android Studio, Ronomepo, or Empty preset.
**Project workspaces** manages the repeated terminal setup as a simple table of
workspace numbers and project folders; folders can be selected individually or
pasted one per line and numbered automatically. Raw commands and window-match
rules are generated automatically for Terminal, Chromium, VS Code, Android
Studio, and Ronomepo, and remain hidden behind **Advanced** unless a genuinely
custom application is needed. Template terminals can be added in a batch by
supplying only a count and working directory.

**Compose layout** opens a visual nested-layout editor. Any application slot
can be split side-by-side or top/bottom, then split again recursively. This
supports arrangements such as one application in a left column and two stacked
applications in a right column without manually writing i3 layout JSON.

Before replacing the configuration, every save creates a timestamped backup in
`~/.local/state/i3-workspace-config/backups/`. The newest 20 backups are kept.

Templates use `{{parameter}}` in any string field. For example, the included
`project-terminals` template uses `{{path}}` as all three working directories. In
the template editor, define the template's parameters, layout, and applications
directly. Then add materialized workspaces beneath it and provide a concrete
value for each parameter. Materialized workspaces appear in the main list with
their source template and resolved contents.

To discard every window on the currently focused workspace and recreate that
workspace from the configuration, run:

```bash
resetworkspace
```

This command intentionally closes all applications on that workspace. It
refuses to act when the focused workspace is neither configured nor recorded
as a session project. The detached
reset worker logs to `~/.local/state/i3-workspace-reset.log`, since it also
closes the terminal from which it was invoked.
Reset waits up to 30 seconds for the old windows to close before recreating
the workspace. If an application refuses to close, reset stops; resolve any
close dialogs and retry. Resets from the bar also write to the same log.

To create a remembered three-terminal project workspace, pass a project path
to `projectworkspace`:

```bash
projectworkspace rns-rs
projectworkspace /tmp/another-project
```

A relative path is resolved below `/home/lelloman/lelloprojects`; an absolute
path is used directly. The workspace is named after the directory and is
remembered for the next login. Close its windows and leave the empty workspace
to remove it from the saved session. `reset` also works for session projects.

The i3bar keeps the normal `i3status` information and adds clickable
`+ project` and `reset` controls. The project control opens a `dmenu` folder
picker, and reset shows a confirmation dialog before closing any windows.
The same controls are available with `Mod+P` (project picker) and `Mod+R`
(reset with confirmation). Use `Mod+Ctrl+R` to enter or leave resize mode.

---

### Codex workspace notifications

Stow both `bash` and `scripts` to make new `codex` sessions mark their i3
workspace red when Codex emits a notification while unfocused. This includes
turn completion and approval notifications; all TUI notification types are
enabled. Focusing the requesting terminal clears i3's urgency hint. Switching
to its workspace normally focuses that terminal; with multiple windows you may
need to focus the requesting terminal explicitly.

The `codex-i3` launcher requires Python 3, `xdotool`, Codex on `PATH`, and an X11
session. It relays Codex through a pseudo-terminal and converts notification
bells to window urgency, excluding bells that terminate terminal title updates.
It uses `WINDOWID` when available, otherwise the active window at launch, so
start it from the focused terminal. Resizing and the child exit status are
forwarded. Non-terminal invocations and sessions without `DISPLAY` run Codex
directly. This integration targets i3/X11, not native Wayland windows.

Notification settings are passed by the launcher; no personal Codex config is
tracked or required. Use `command codex` to bypass the launcher. After stowing,
open a new terminal or run `source ~/.bash_aliases`, then restart any existing
Codex sessions. The normal i3bar urgent-workspace colour is already red.

---

### sway and waybar

Wayland equivalents of the i3 and i3bar/i3status setup.

**Stows to:** `~/.config/sway/` and `~/.config/waybar/`

The Sway setup preserves the i3 key bindings, output-local workspace cycling,
application assignments, terminal grid layouts, ordered monitor/workspace
startup, volume controls, locking, and screenshot actions. Native Wayland
clients are matched by `app_id`; XWayland clients retain class fallbacks.

Install the Ubuntu dependencies with:

```bash
sudo apt-get update
sudo apt-get install sway swaybg swayidle swaylock waybar grim slurp \
  wl-clipboard fuzzel xwayland xdg-desktop-portal-wlr jq dex \
  network-manager-gnome pulseaudio-utils
```

The existing i3 package remains installed as a fallback session. Sway startup
output is written to `~/.local/state/sway-startup.log`.

On Ubuntu 24.04 with the proprietary NVIDIA driver, install the additional
session entry after cloning this repository:

```bash
sudo cp system/usr/share/wayland-sessions/sway-nvidia.desktop \
  /usr/share/wayland-sessions/
```

Select **Sway (NVIDIA)** from the login screen. This is kept separate from the
package-provided Sway entry and can be removed without modifying package files.

---

### claude

Claude Code configuration.

**Stows to:** `~/.claude/`

**Contents:**
- `settings.json` - statusline and plugins config
- `statusline.sh` - custom statusline script
- `commands/` - custom slash commands

**Note:** Stow cannot symlink files into existing directories. After running `stow claude`, manually create symlinks:
```bash
ln -sf ~/dotfiles/claude/.claude/statusline.sh ~/.claude/statusline.sh
ln -sfn ~/dotfiles/claude/.claude/commands ~/.claude/commands
```

---

### pezzotticlaude

Claude Code configuration for alternative API endpoint (e.g., MiniMax).

**Stows to:** `~/.pezzotticlaude/`

**Contents:**
- `.claude.json.template` - app state template (skip-onboarding, etc.)
- `.claude.json` - runtime state (gitignored, auto-generated)
- `settings.json.template` - config template (statusline, plugins)
- `settings.json` - actual config with API key (gitignored)
- `statusline.sh` - custom statusline script
- `commands/` - custom slash commands (shared with claude)

**Note:** Stow cannot symlink files into existing directories. After running `stow pezzotticlaude`, manually create symlinks:
```bash
ln -sf ~/dotfiles/pezzotticlaude/.pezzotticlaude/statusline.sh ~/.pezzotticlaude/statusline.sh
ln -sfn ~/dotfiles/pezzotticlaude/.pezzotticlaude/commands ~/.pezzotticlaude/commands
```

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

### vim

Vim configuration.

**Stows to:** `~/.vimrc`

**Contents:**
- Relative line numbers (shows current line absolute, others as deltas)

---

### scripts

Custom scripts.

**Stows to:** `~/.local/bin/`

**Contents:**
- `codex-i3` - bridge Codex terminal notifications to i3 workspace urgency
- `confmonitor` - monitor layout setup script
- `i3-session-startup` - ordered i3 startup script
- `setupworkspaces` - i3 workspace setup script
- `configure-workspaces` - GUI for workspace, display, layout, and template setup
- `resetworkspace` - clear and recreate the focused i3 workspace
- `projectworkspace PATH` - create an ephemeral three-terminal project workspace
- `i3status-controls` / `i3bar-control` - clickable workspace controls for i3bar
- `workspace-configurator` - shared configuration/setup engine
- `confmonitor-sway` - Sway output layout setup script
- `sway-session-startup` - ordered Sway startup script
- `setupworkspaces-sway` - Sway workspace/application setup script
- `sway-screenshot` - Wayland file and clipboard screenshot helper
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
