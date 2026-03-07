import sqlite3
from pathlib import Path
from datetime import date


def get_connection(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            text         TEXT NOT NULL,
            project      TEXT,
            status       TEXT DEFAULT 'pending',
            priority     INTEGER DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            due_date     DATE
        );
    ''')
    conn.commit()
    conn.close()


def add_item(db_path, text, project=None, priority=0):
    conn = get_connection(db_path)
    cursor = conn.execute(
        'INSERT INTO items (text, project, priority) VALUES (?, ?, ?)',
        (text, project, priority),
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


def get_items(db_path, status='pending', limit=None, project=None, today_only=False):
    conn = get_connection(db_path)
    query = 'SELECT * FROM items WHERE status = ?'
    params = [status]

    if project:
        query += ' AND project = ?'
        params.append(project)

    if today_only:
        today = date.today().isoformat()
        query += ' AND DATE(created_at) = ?'
        params.append(today)

    query += ' ORDER BY priority DESC, created_at ASC'

    if limit is not None:
        query += ' LIMIT ?'
        params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_all_items(db_path, project=None):
    """Return pending + done items, pending first."""
    conn = get_connection(db_path)
    query = 'SELECT * FROM items'
    params = []
    if project:
        query += ' WHERE project = ?'
        params.append(project)
    query += ' ORDER BY status ASC, priority DESC, created_at ASC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def complete_item(db_path, item_id):
    conn = get_connection(db_path)
    conn.execute(
        'UPDATE items SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
        ('done', item_id),
    )
    conn.commit()
    conn.close()


def reopen_item(db_path, item_id):
    conn = get_connection(db_path)
    conn.execute(
        "UPDATE items SET status = 'pending', completed_at = NULL WHERE id = ?",
        (item_id,),
    )
    conn.commit()
    conn.close()


def delete_item(db_path, item_id):
    conn = get_connection(db_path)
    conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()


def update_item(db_path, item_id, text=None, project=None, priority=None):
    conn = get_connection(db_path)
    if text is not None:
        conn.execute('UPDATE items SET text = ? WHERE id = ?', (text, item_id))
    if project is not None:
        conn.execute('UPDATE items SET project = ? WHERE id = ?', (project, item_id))
    if priority is not None:
        conn.execute('UPDATE items SET priority = ? WHERE id = ?', (priority, item_id))
    conn.commit()
    conn.close()


def count_items(db_path, status='pending', project=None):
    conn = get_connection(db_path)
    query = 'SELECT COUNT(*) FROM items WHERE status = ?'
    params = [status]
    if project:
        query += ' AND project = ?'
        params.append(project)
    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return count
