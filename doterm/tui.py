import curses
import textwrap
from . import db as database


def run_tui(db_path, project_filter=None):
    curses.wrapper(lambda stdscr: _run(stdscr, db_path, project_filter))


def _prompt(stdscr, h, w, prompt_text, default=''):
    curses.echo()
    curses.curs_set(1)
    stdscr.addstr(h - 1, 0, ' ' * (w - 1))
    stdscr.addstr(h - 1, 0, prompt_text)
    stdscr.refresh()

    result = list(default)
    stdscr.addstr(h - 1, len(prompt_text), ''.join(result))
    stdscr.move(h - 1, len(prompt_text) + len(result))

    while True:
        ch = stdscr.getch()
        if ch in (10, 13):
            break
        elif ch == 27:
            result = list(default)
            break
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if result:
                result.pop()
                col = len(prompt_text)
                stdscr.addstr(h - 1, col, ' ' * (w - col - 1))
                stdscr.addstr(h - 1, col, ''.join(result))
                stdscr.move(h - 1, col + len(result))
        elif 32 <= ch < 127:
            result.append(chr(ch))
            stdscr.addstr(h - 1, len(prompt_text), ''.join(result))
            stdscr.move(h - 1, len(prompt_text) + len(result))
        stdscr.refresh()

    curses.noecho()
    curses.curs_set(0)
    return ''.join(result)


def _run(stdscr, db_path, project_filter):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # done
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # selected
    curses.init_pair(3, curses.COLOR_WHITE, -1)   # normal
    curses.init_pair(4, curses.COLOR_CYAN, -1)    # header/accent
    curses.init_pair(5, curses.COLOR_RED, -1)     # deleted/error
    curses.init_pair(6, curses.COLOR_YELLOW, -1)  # message

    show_done = False
    current = 0
    offset = 0
    message = ''
    active_project = project_filter

    def load_items():
        if show_done:
            return list(database.get_all_items(db_path, project=active_project))
        return list(database.get_items(db_path, project=active_project))

    items = load_items()

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        visible_rows = h - 3  # 1 header + 1 footer help + 1 status bar

        # Clamp current
        if items:
            current = max(0, min(current, len(items) - 1))

        # Scroll offset
        if items:
            if current < offset:
                offset = current
            elif current >= offset + visible_rows:
                offset = current - visible_rows + 1

        # --- Header ---
        title = ' doterm'
        if active_project:
            title += f' [{active_project}]'
        if show_done:
            title += ' (all)'
        title_right = f'{len(items)} items '
        stdscr.addstr(0, 0, title, curses.color_pair(4) | curses.A_BOLD)
        if len(title_right) < w:
            stdscr.addstr(0, w - len(title_right), title_right, curses.color_pair(4))

        # --- Items ---
        for i, item in enumerate(items[offset:offset + visible_rows]):
            row = i + 1
            idx = i + offset
            is_selected = idx == current

            done = item['status'] == 'done'
            check = '[x]' if done else '[ ]'
            proj = f' ({item["project"]})' if item['project'] and not active_project else ''
            note_flag = ' »' if item['note'] else ''
            line = f' {check}{proj} {item["text"]}{note_flag}'
            line = line[:w - 1]

            if is_selected:
                attr = curses.color_pair(2) | curses.A_BOLD
            elif done:
                attr = curses.color_pair(1)
            else:
                attr = curses.color_pair(3)

            stdscr.addstr(row, 0, line.ljust(w - 1), attr)

        if not items:
            hint = ' No items. Press "a" to add one.'
            stdscr.addstr(2, 0, hint[:w - 1], curses.color_pair(3))

        # --- Status / message bar ---
        if message:
            stdscr.addstr(h - 2, 0, (' ' + message)[:w - 1], curses.color_pair(6))
            message = ''
        else:
            if items:
                pos = f' {current + 1}/{len(items)}'
                stdscr.addstr(h - 2, 0, pos, curses.color_pair(4))

        # --- Help bar ---
        help_text = ' j/k:nav  space:done  l:note  a:add  e:edit  p:project  D:delete  s:show-done  q:quit'
        stdscr.addstr(h - 1, 0, help_text[:w - 1], curses.color_pair(4))

        stdscr.refresh()
        key = stdscr.getch()

        if key in (ord('q'), 27):
            break

        elif key in (ord('j'), curses.KEY_DOWN):
            if items and current < len(items) - 1:
                current += 1

        elif key in (ord('k'), curses.KEY_UP):
            if current > 0:
                current -= 1

        elif key == ord('g'):
            current = 0

        elif key == ord('G'):
            current = max(0, len(items) - 1)

        elif key == curses.KEY_PPAGE:  # page up
            current = max(0, current - visible_rows)

        elif key == curses.KEY_NPAGE:  # page down
            current = min(max(0, len(items) - 1), current + visible_rows)

        elif key == ord(' '):
            if items:
                item = items[current]
                if item['status'] == 'pending':
                    database.complete_item(db_path, item['id'])
                    message = f'Done: {item["text"][:50]}'
                else:
                    database.reopen_item(db_path, item['id'])
                    message = f'Reopened: {item["text"][:50]}'
                items = load_items()

        elif key == ord('a'):
            text = _prompt(stdscr, h, w, 'New item: ')
            if text.strip():
                database.add_item(db_path, text.strip(), project=active_project)
                items = load_items()
                current = len(items) - 1
                message = f'Added: {text.strip()[:50]}'

        elif key == ord('e'):
            if items:
                item = items[current]
                text = _prompt(stdscr, h, w, 'Edit: ', item['text'])
                if text.strip() and text != item['text']:
                    database.update_item(db_path, item['id'], text=text.strip())
                    items = load_items()
                    message = 'Updated.'

        elif key == ord('D'):
            if items:
                item = items[current]
                confirm = _prompt(stdscr, h, w, f'Delete "{item["text"][:40]}"? [y/N]: ')
                if confirm.lower() == 'y':
                    database.delete_item(db_path, item['id'])
                    items = load_items()
                    current = min(current, max(0, len(items) - 1))
                    message = 'Deleted.'

        elif key == ord('p'):
            proj = _prompt(stdscr, h, w, 'Project filter (blank=all): ')
            active_project = proj.strip() or None
            items = load_items()
            current = 0

        elif key == ord('s'):
            show_done = not show_done
            items = load_items()
            current = 0

        elif key == ord('l'):
            if items:
                _detail_view(stdscr, db_path, items[current])
                items = load_items()

        elif key == ord('r'):
            items = load_items()


def _detail_view(stdscr, db_path, item):
    """Drill-in note view for a single item. h returns to list."""
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Reload item so edits are reflected immediately
        from . import db as database
        fresh = database.get_item(db_path, item['id'])
        if fresh is None:
            break
        item = fresh

        # Header: item title
        done = item['status'] == 'done'
        check = '[x]' if done else '[ ]'
        proj = f' [{item["project"]}]' if item['project'] else ''
        title = f' {check}{proj} {item["text"]}'
        stdscr.addstr(0, 0, title[:w - 1], curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 0, '─' * (w - 1), curses.color_pair(4))

        # Note body (word-wrapped)
        note = item['note'] or ''
        if note:
            row = 2
            for para in note.splitlines() or ['']:
                for line in (textwrap.wrap(para, w - 2) or ['']):
                    if row >= h - 2:
                        break
                    stdscr.addstr(row, 1, line, curses.color_pair(3))
                    row += 1
        else:
            stdscr.addstr(3, 1, '(no note)  press e to add one', curses.color_pair(3))

        # Help bar
        help_text = ' h:back  e:edit note  q:quit'
        stdscr.addstr(h - 1, 0, help_text[:w - 1], curses.color_pair(4))

        stdscr.refresh()
        key = stdscr.getch()

        if key in (ord('h'), ord('q'), 27):
            break

        elif key == ord('e'):
            new_note = _prompt(stdscr, h, w, 'Note: ', item['note'] or '')
            database.update_note(db_path, item['id'], new_note or None)
