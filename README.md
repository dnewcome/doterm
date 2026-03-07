# doterm

A fast, terminal-based todo list with a curses TUI and vim-style navigation. Built for developers who live in the terminal and want frictionless task management without leaving the command line.

- Add items as fast as a git commit
- Project-aware task organization
- SQLite storage — no server, no sync, just a file
- Curses TUI with vim keybindings for interactive management
- Configurable via `~/.doterm.rc`

---

## Requirements

- Python 3.8+
- One of: `pipx`, `uv`, or a virtualenv with `pip`

---

## Installation

### With pipx (recommended)

```sh
pipx install /path/to/doterm
```

### With uv into a virtualenv

```sh
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

### With pip in a virtualenv

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Building from source

```sh
git clone <repo>
cd doterm
pipx install .
```

For development (editable install):

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Configuration

Copy the example config to your home directory:

```sh
cp doterm.rc.example ~/.doterm.rc
```

**`~/.doterm.rc`:**

```ini
[display]
# Number of items shown by `doterm` with no flags
max_items = 5

[storage]
# Path to the SQLite database file
db_path = ~/doterm.sqlite
```

All settings have defaults, so the config file is optional.

---

## Quick start

```sh
# Add some items
doterm -m "Review pull requests"
doterm -m "Fix login bug" -p auth
doterm -m "Set up CI pipeline" -p devops

# Show top 5 pending items
doterm

# Show all pending items
doterm -a

# Open the interactive TUI
doterm -i
```

---

## CLI reference

### Add an item

```sh
doterm -m "task description"
doterm -m "task description" -p project-name
```

### List items

```sh
doterm                  # show top N pending items (N from config, default 5)
doterm -a               # show all pending items
doterm -n 10            # show top 10
doterm -p auth          # filter by project
doterm -t               # show only items created today
doterm --done           # show completed items
doterm -p auth --done   # completed items in a project
```

### Interactive TUI

```sh
doterm -i               # open TUI
doterm -i -p auth       # open TUI filtered to a project
```

### All flags

| Flag | Long form | Description |
|---|---|---|
| `-m TEXT` | `--message TEXT` | Add a new todo item |
| `-a` | `--all` | Show all pending items (no limit) |
| `-i` | `--interactive` | Open interactive curses TUI |
| `-p NAME` | `--project NAME` | Assign to / filter by project |
| `-t` | `--today` | Show only items created today |
| `-n N` | | Override number of items to display |
| | `--done` | Show completed items instead of pending |

---

## Interactive TUI

Launch with `doterm -i`.

```
 doterm [auth]                                   4 items
 [ ] Fix login bug
 [x] Add OAuth provider
 [ ] Write unit tests
 [ ] Update session expiry logic

 3/4
 j/k:nav  space:done  a:add  e:edit  p:project  D:delete  s:show-done  q:quit
```

### Keybindings

| Key | Action |
|---|---|
| `j` / `down` | Move down |
| `k` / `up` | Move up |
| `g` | Jump to top |
| `G` | Jump to bottom |
| `PgUp` / `PgDn` | Page up / down |
| `space` | Toggle item done / pending |
| `a` | Add new item |
| `e` | Edit current item |
| `D` | Delete current item (prompts for confirmation) |
| `p` | Set project filter (blank to show all) |
| `s` | Toggle display of completed items |
| `r` | Refresh list from database |
| `q` / `ESC` | Quit |

---

## Use cases

### Daily standup prep

Check what you worked on yesterday and what's next:

```sh
doterm --done   # what you completed
doterm -a       # what's still pending
```

### Project-scoped task lists

Keep work separated by project, then drill in:

```sh
doterm -m "Design new onboarding flow" -p frontend
doterm -m "Migrate users table" -p backend
doterm -m "Write API docs" -p backend

doterm -p backend          # show backend tasks
doterm -i -p backend       # interactive view for backend only
```

### Capture tasks without breaking flow

Add items from anywhere without opening an editor:

```sh
doterm -m "follow up with @alice about deployment window"
doterm -m "check if the rate limiter is correctly scoped" -p backend
```

### Quick daily focus list

Set your config to `max_items = 3` and run `doterm` to see only your top priorities each time you open a terminal.

---

## Storage

All data is stored in a single SQLite file (default: `~/doterm.sqlite`). You can change the path in `~/.doterm.rc`.

The database contains two tables:

- **`items`** — id, text, project, status, priority, created\_at, completed\_at, due\_date
- **`projects`** — id, name, created\_at

You can query or manipulate the database directly with any SQLite client if needed.

---

## Roadmap

- Shell history integration and activity reports
- Time tracking per item
- Priority management (promote/demote items in TUI)
- Due dates and overdue highlighting
- External source sync (Jira, GitHub Issues)
- Export to markdown / daily report generation
