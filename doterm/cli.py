import argparse
import sys
from . import db as database
from .config import load_config, get_db_path, get_max_items
from .tui import run_tui


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
                        help='Show all pending items (no limit)')
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
    status = 'done' if args.done else 'pending'
    limit = None if (args.all or args.done) else (args.n or get_max_items(config))

    items = list(database.get_items(
        db_path,
        status=status,
        limit=limit,
        project=args.project,
        today_only=args.today,
    ))

    if not items:
        if args.done:
            print('No completed items.')
        else:
            print('No pending items.  Add one with:  doterm -m "your task"')
        return

    total = database.count_items(db_path, status=status, project=args.project)
    shown = len(items)

    # -d alone (no value) → args.detail is True (the const); show notes inline
    show_notes = args.detail is not None

    print()
    for i, item in enumerate(items, 1):
        print(_fmt(item, i, show_detail=show_notes))
    print()

    if limit is not None and total > shown:
        print(f'  ... {total - shown} more hidden  (use -a to show all, -i for TUI)')
        print()


if __name__ == '__main__':
    main()
