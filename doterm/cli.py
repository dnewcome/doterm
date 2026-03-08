import argparse
import sqlite3
import sys
from . import db as database
from .config import load_config, get_db_path, get_max_items
from .tui import run_tui


def _md_table(cursor):
    """Render a cursor result as a markdown table. Returns empty string if no rows."""
    if cursor.description is None:
        return f'*{cursor.rowcount} row(s) affected*\n'

    cols = [d[0] for d in cursor.description]
    rows = [[str(v) if v is not None else '' for v in row] for row in cursor.fetchall()]

    if not rows:
        return '*no results*\n'

    widths = [len(c) for c in cols]
    for row in rows:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))

    def fmt_row(cells):
        return '| ' + ' | '.join(c.ljust(widths[i]) for i, c in enumerate(cells)) + ' |'

    lines = [
        fmt_row(cols),
        '| ' + ' | '.join('-' * w for w in widths) + ' |',
    ]
    for row in rows:
        lines.append(fmt_row(row))
    return '\n'.join(lines) + '\n'


def _run_sql_report(db_path, sql):
    """Execute one or more SQL statements from stdin and print a markdown report."""
    conn = database.get_connection(db_path)
    # Split blocks on blank lines; each block may start with -- comment as heading
    blocks = [b.strip() for b in sql.split('\n\n') if b.strip()]
    try:
        for block in blocks:
            lines = block.splitlines()
            heading_lines = []
            sql_lines = []
            for line in lines:
                if line.startswith('--') and not sql_lines:
                    heading_lines.append(line.lstrip('- ').strip())
                else:
                    sql_lines.append(line)

            heading = ' '.join(heading_lines)
            statement = ' '.join(sql_lines).rstrip(';').strip()
            if not statement:
                continue

            if heading:
                print(f'## {heading}\n')

            try:
                cursor = conn.execute(statement)
                print(_md_table(cursor))
            except sqlite3.Error as e:
                print(f'*Error: {e}*\n', file=sys.stderr)
    finally:
        conn.close()


def _fmt(item, index, show_detail=False):
    status = 'x' if item['status'] == 'done' else ' '
    project = f'({item["project"]}) ' if item['project'] else ''
    note_flag = ' »' if item['note'] else ''
    line = f'  {index:3}. [{status}] {project}{item["text"]}{note_flag}'
    if show_detail and item['note']:
        line += f'\n         {item["note"]}'
    return line


def main():
    parser = argparse.ArgumentParser(
        prog='doterm',
        description='Fast terminal todo list',
    )
    parser.add_argument('-m', '--message', metavar='TEXT',
                        help='Add a new todo item')
    parser.add_argument('-a', '--all', action='store_true',
                        help='Show all items including done (no limit)')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Open interactive TUI')
    parser.add_argument('-p', '--project', metavar='NAME',
                        help='Assign to / filter by project')
    parser.add_argument('-t', '--today', action='store_true',
                        help='Show only items created today')
    parser.add_argument('--done', action='store_true',
                        help='Show completed items')
    parser.add_argument('-d', '--detail', nargs='?', const=True, metavar='TEXT',
                        help='With -m: attach a note. Alone: show notes inline when listing.')
    parser.add_argument('-n', metavar='N', type=int,
                        help='Override number of items to show')

    args = parser.parse_args()

    config = load_config()
    db_path = get_db_path(config)
    database.init_db(db_path)

    # SQL report mode: pipe SQL via stdin
    if not sys.stdin.isatty():
        sql = sys.stdin.read().strip()
        if sql:
            _run_sql_report(db_path, sql)
        return

    # Add item
    if args.message:
        note = args.detail if isinstance(args.detail, str) else None
        item_id = database.add_item(db_path, args.message, project=args.project, note=note)
        project_tag = f' [{args.project}]' if args.project else ''
        detail_tag = ' (with note)' if note else ''
        print(f'Added #{item_id}{project_tag}{detail_tag}: {args.message}')
        return

    # Interactive mode
    if args.interactive:
        run_tui(db_path, project_filter=args.project)
        return

    # List items
    if args.all:
        items = list(database.get_all_items(db_path, project=args.project))
        limit = None
    elif args.done:
        items = list(database.get_items(db_path, status='done', project=args.project))
        limit = None
    else:
        limit = args.n or get_max_items(config)
        items = list(database.get_items(
            db_path,
            status='pending',
            limit=limit,
            project=args.project,
            today_only=args.today,
        ))

    if not items:
        if args.done:
            print('No completed items.')
        elif args.all:
            print('No items.  Add one with:  doterm -m "your task"')
        else:
            print('No pending items.  Add one with:  doterm -m "your task"')
        return

    total = database.count_items(db_path, status='pending', project=args.project)
    shown = len(items)

    # -d alone (no value) → args.detail is True (the const); show notes inline
    show_notes = args.detail is not None

    print()
    for i, item in enumerate(items, 1):
        print(_fmt(item, i, show_detail=show_notes))
    print()

    if not args.all and not args.done and limit is not None and total > shown:
        print(f'  ... {total - shown} more hidden  (use -a to show all, -i for TUI)')
        print()


if __name__ == '__main__':
    main()
