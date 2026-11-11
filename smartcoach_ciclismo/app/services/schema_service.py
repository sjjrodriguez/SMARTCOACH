"""Adds columns introduced after the first deploy.

db.create_all() creates missing tables but never alters existing ones, so
databases created before a model change (e.g. Supabase) need the new columns
added. Safe to run on every start: it only touches columns that are missing.
"""
from sqlalchemy import inspect, text

# table -> {column: SQL type}
REQUIRED_COLUMNS = {
    'training_plans': {'birth_date': 'DATE', 'change_reason': 'TEXT'},
}


def ensure_columns(db, logger=None):
    try:
        inspector = inspect(db.engine)
        for table, columns in REQUIRED_COLUMNS.items():
            if not inspector.has_table(table):
                continue
            existing = {c['name'] for c in inspector.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {sql_type}'))
        db.session.commit()
    except Exception:  # never block the app from starting
        db.session.rollback()
        if logger:
            logger.exception('Could not update the database schema')
