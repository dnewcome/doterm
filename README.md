# doterm

A fast, terminal-based todo list with a curses TUI and vim-style navigation. Built for developers who live in the terminal and want frictionless task management without leaving the command line.

- Add items as fast as a git commit
- Project-aware task organization
- Notes/detail attached to any item, viewable inline or in a drill-down view
- Done items shown alongside pending by default — full picture at a glance
- Manual reordering with Shift-J/K in the TUI
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

# Add an item with a note
doterm -m "Investigate auth token expiry" -p auth -d "Check JWT decode path in middleware.py"

# Show top 5 pending items
doterm

# Show all items (pending + done)
doterm -a

# Show notes inline
doterm -d

# Open the interactive TUI
doterm -i
```

---

## CLI reference

### Add an item

```sh
doterm -m "task description"
doterm -m "task description" -p project-name

# Add with a note/detail attached
doterm -m "task description" -d "fuller context or acceptance criteria"
```

### List items

```sh
doterm                  # show top N pending items (N from config, default 5)
doterm -a               # show all items — pending and done together
doterm -d               # show pending items with notes expanded inline
doterm -n 10            # show top 10 pending
doterm -p auth          # filter by project
doterm -t               # show only items created today
doterm --done           # show completed items only
doterm -p auth --done   # completed items in a project
```

Items that have a note attached are marked with `»` in all list output.

### Interactive TUI

```sh
doterm -i               # open TUI
doterm -i -p auth       # open TUI filtered to a project
```

### SQL reports

Pipe any SQL into `doterm` and get a markdown report back. Blocks separated by a blank line are run as separate queries. A leading `-- comment` line becomes a `##` heading.

```sh
echo "SELECT * FROM items WHERE status='pending'" | doterm

# Multi-section report saved to a file
cat <<'EOF' | doterm > report.md
-- Pending items
SELECT id, text, project FROM items WHERE status='pending'

-- Done today
SELECT text, completed_at FROM items
WHERE status='done' AND DATE(completed_at) = DATE('now')

-- Items per project
SELECT COALESCE(project, '(none)') as project,
       COUNT(*) as total,
       SUM(status='done') as done
FROM items GROUP BY project ORDER BY total DESC
EOF
```

Output:

```markdown
## Pending items

| id | text                 | project |
| -- | -------------------- | ------- |
| 1  | Write project README |         |
| 2  | Set up CI pipeline   | devops  |

## Items per project

| project | total | done |
| ------- | ----- | ---- |
| auth    | 4     | 1    |
| devops  | 2     | 0    |
```

The database schema available to query:

| Table | Columns |
|---|---|
| `items` | `id`, `text`, `note`, `project`, `status`, `priority`, `position`, `created_at`, `completed_at`, `due_date` |
| `projects` | `id`, `name`, `created_at` |

### All flags

| Flag | Long form | Description |
|---|---|---|
| `-m TEXT` | `--message TEXT` | Add a new todo item |
| `-a` | `--all` | Show all items including done (no limit) |
| `-i` | `--interactive` | Open interactive curses TUI |
| `-p NAME` | `--project NAME` | Assign to / filter by project |
| `-d [TEXT]` | `--detail [TEXT]` | With `-m`: attach a note. Alone: show notes inline. |
| `-t` | `--today` | Show only items created today |
| `-n N` | | Override number of items to display |
| | `--done` | Show completed items only |

---

## Interactive TUI

Launch with `doterm -i`.

```
 doterm [auth]                                   4 items
 [ ] Fix login bug
 [x] Add OAuth provider »
 [ ] Write unit tests
 [ ] Update session expiry logic

 3/4
 j/k:nav  J/K:move  space:done  l:note  a:add  e:edit  p:project  D:delete  s:hide-done  q:quit
```

Done items (`[x]`) are shown alongside pending by default. Items marked with `»` have a note attached.

### Keybindings

| Key | Action |
|---|---|
| `j` / `down` | Move cursor down |
| `k` / `up` | Move cursor up |
| `g` | Jump to top |
| `G` | Jump to bottom |
| `PgUp` / `PgDn` | Page up / down |
| `J` (Shift-J) | Move current item down in the list |
| `K` (Shift-K) | Move current item up in the list |
| `space` | Toggle item done / pending |
| `l` | Drill into note view for current item |
| `a` | Add new item |
| `e` | Edit current item text |
| `D` | Delete current item (prompts for confirmation) |
| `p` | Set project filter (blank to show all) |
| `s` | Toggle hiding done items |
| `r` | Refresh list from database |
| `q` / `ESC` | Quit |

### Note view

Press `l` on any item to open its note. Press `h`, `q`, or `ESC` to return to the list.

```
 [ ] Investigate auth token expiry
─────────────────────────────────────────────────
 Check JWT decode path in middleware.py — tokens
 may not be refreshed on 401.

 h:back  e:edit note  q:quit
```

| Key | Action |
|---|---|
| `e` | Edit the note text |
| `h` / `q` / `ESC` | Return to list |

---

## Use cases

### Daily standup prep

Check what you completed and what's still open in one shot:

```sh
doterm -a       # all items — done and pending together, in your order
doterm --done   # completed items only
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

### Attach context to a task

Keep acceptance criteria, links, or investigation notes right next to the task:

```sh
doterm -m "Migrate users table" -p backend -d "See RFC in Notion. Must be zero-downtime."
doterm -d    # show all notes inline
```

In the TUI, press `l` to open the note, `e` to edit it, `h` to go back.

### Reorder your list

Use `J`/`K` in the TUI to promote or demote items. The order is persisted to the database and reflected in CLI output.

### Quick daily focus list

Set your config to `max_items = 3` and run `doterm` to see only your top priorities each time you open a terminal. Use `J`/`K` in the TUI to put the most important items at the top.

---

## Storage

All data is stored in a single SQLite file (default: `~/doterm.sqlite`). You can change the path in `~/.doterm.rc`.

The database contains two tables:

- **`items`** — id, text, note, project, status, priority, position, created\_at, completed\_at, due\_date
- **`projects`** — id, name, created\_at

You can query or manipulate the database directly with any SQLite client if needed.

---

## Roadmap

- Shell history integration and activity reports
- Time tracking per item
- Due dates and overdue highlighting
- External source sync (Jira, GitHub Issues)
- Export to markdown / daily report generation
