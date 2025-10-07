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

    # Table for daily member count tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS member_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            member_count INTEGER NOT NULL,
            date DATE NOT NULL,
            UNIQUE(guild_id, date)
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

def log_member_count(guild_id, member_count):
    """Logs the current member count for a guild for the current date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().date()
    # Use INSERT OR REPLACE to avoid duplicate entries for the same day
    cursor.execute(
        "INSERT OR REPLACE INTO member_counts (guild_id, member_count, date) VALUES (?, ?, ?)",
        (guild_id, member_count, today)
    )
    conn.commit()
    conn.close()

def get_member_count_history(guild_id):
    """Retrieves the member count history for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, member_count FROM member_counts WHERE guild_id = ? ORDER BY date ASC",
        (guild_id,)
    )
    history = cursor.fetchall()
    conn.close()
    return history

def get_top_active_users(guild_id, limit=10):
    """
    Calculates a combined activity score for users and returns the top 10.
    Score is a weighted combination of messages sent and time in voice channels.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Weights for scoring: 1 point per message, 1 point per 10 seconds in voice
    # These can be adjusted to change the ranking logic.
    query = """
        SELECT
            user_id,
            SUM(message_score) AS total_message_score,
            SUM(voice_score) AS total_voice_score,
            SUM(message_score) + SUM(voice_score) AS combined_score
        FROM (
            -- Calculate score from messages
            SELECT
                user_id,
                COUNT(*) * 1.0 AS message_score,
                0 AS voice_score
            FROM messages
            WHERE guild_id = ?
            GROUP BY user_id

            UNION ALL

            -- Calculate score from voice sessions
            SELECT
                user_id,
                0 AS message_score,
                SUM(strftime('%s', session_end) - strftime('%s', session_start)) / 10.0 AS voice_score
            FROM voice_sessions
            WHERE guild_id = ?
            GROUP BY user_id
        )
        GROUP BY user_id
        ORDER BY combined_score DESC
        LIMIT ?
    """

    cursor.execute(query, (guild_id, guild_id, limit))
    top_users = cursor.fetchall()
    conn.close()
    return top_users