"""Application settings, read from environment variables (or from the .env file).

Nothing secret lives in the code: the database address and the secret key come from the
environment. Copy .env.example to .env and fill it in.

    DATABASE_URL  e.g. postgresql+psycopg2://user:password@host:6543/postgres
                  If it is missing the app falls back to a local SQLite file, so the
                  project always starts for development.
    SECRET_KEY    signs the session cookie. Use a long random value in production.
    FLASK_DEBUG   "1" turns debug mode on when you start the app with `python run.py`.
"""
import os

DEFAULT_SECRET_KEY = 'dev-key-secreta'
DEFAULT_DATABASE_URL = 'sqlite:///smartcoach.db'


def _database_url():
    url = os.getenv('DATABASE_URL') or DEFAULT_DATABASE_URL
    # Some providers still hand out "postgres://", which SQLAlchemy no longer accepts.
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg2://' + url[len('postgres://'):]
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or DEFAULT_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Supabase's pooler closes idle connections; check them before reusing.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
