import sqlite3
from datetime import datetime

DB_NAME = 'bot_stats.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for message tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL
        )
    ''')

    # Table for voice activity tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            session_start TIMESTAMP NOT NULL,
            session_end TIMESTAMP NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def log_message(user_id, guild_id):
    """Logs a message sent by a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, guild_id, timestamp) VALUES (?, ?, ?)",
        (user_id, guild_id, datetime.utcnow())
    )
    conn.commit()
    conn.close()

def log_voice_session(user_id, guild_id, start_time, end_time):
    """Logs a completed voice session for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO voice_sessions (user_id, guild_id, session_start, session_end) VALUES (?, ?, ?, ?)",
        (user_id, guild_id, start_time, end_time)
    )
    conn.commit()
    conn.close()

def get_message_stats(guild_id, period='all'):
    """Retrieves message statistics for all users in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT user_id, COUNT(*) as message_count FROM messages WHERE guild_id = ?"
    params = [guild_id]

    if period != 'all':
        query += " AND timestamp >= ?"
        params.append(datetime.utcnow() - _get_timedelta(period))

    query += " GROUP BY user_id ORDER BY message_count DESC"

    cursor.execute(query, params)
    stats = cursor.fetchall()
    conn.close()
    return stats

def get_voice_stats(guild_id, period='all'):
    """Retrieves voice activity statistics for all users in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT user_id, SUM(strftime('%s', session_end) - strftime('%s', session_start)) as total_seconds FROM voice_sessions WHERE guild_id = ?"
    params = [guild_id]

    if period != 'all':
        query += " AND session_start >= ?"
        params.append(datetime.utcnow() - _get_timedelta(period))

    query += " GROUP BY user_id ORDER BY total_seconds DESC"

    cursor.execute(query, params)
    stats = cursor.fetchall()
    conn.close()
    return stats

def _get_timedelta(period):
    """Helper function to get a timedelta for a given period string."""
    from datetime import timedelta
    if period == 'daily':
        return timedelta(days=1)
    elif period == 'weekly':
        return timedelta(weeks=1)
    elif period == 'monthly':
        # Approximation
        return timedelta(days=30)
    # The 'all' case is handled by the calling functions, which do not call
    # this helper, so no 'else' block is necessary.