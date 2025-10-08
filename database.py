import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_NAME = 'bot_stats.db'

@contextmanager
def get_db_connection():
    """
    Provides a database connection as a context manager,
    handling commits and closing automatically.
    """
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # All table creations are executed within a single transaction
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, timestamp TIMESTAMP NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS voice_sessions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, session_start TIMESTAMP NOT NULL, session_end TIMESTAMP NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS member_counts (id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, member_count INTEGER NOT NULL, date DATE NOT NULL, UNIQUE(guild_id, date))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, audit_log_channel_id INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ar_settings (guild_id INTEGER PRIMARY KEY, is_enabled INTEGER NOT NULL DEFAULT 0, target_channel_id INTEGER, reply_message TEXT NOT NULL DEFAULT 'Cześć, {mention}! Widzę, że pytasz o ustawienia. Wszystkie potrzebne informacje znajdziesz na kanale <#{channel}>.')''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ar_keywords (id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, keyword_type TEXT NOT NULL, keyword TEXT NOT NULL, UNIQUE(guild_id, keyword_type, keyword))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS warn_settings (guild_id INTEGER PRIMARY KEY, warn_limit INTEGER NOT NULL DEFAULT 3, action TEXT NOT NULL DEFAULT 'kick', ban_duration_days INTEGER DEFAULT 7)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (warn_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, moderator_id INTEGER NOT NULL, reason TEXT, timestamp TIMESTAMP NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS active_bans (ban_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, unban_timestamp TIMESTAMP NOT NULL, UNIQUE(guild_id, user_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS economy_settings (guild_id INTEGER PRIMARY KEY, currency_name TEXT NOT NULL DEFAULT 'Points', bet_win_chance INTEGER NOT NULL DEFAULT 45)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS economy_wallets (wallet_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, balance INTEGER NOT NULL DEFAULT 0, UNIQUE(guild_id, user_id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS economy_shop_items (item_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, role_id INTEGER NOT NULL, price INTEGER NOT NULL, UNIQUE(guild_id, role_id))''')

# --- Helper for Time Deltas ---
def _get_timedelta(period: str) -> timedelta:
    if period == 'daily': return timedelta(days=1)
    if period == 'weekly': return timedelta(weeks=1)
    if period == 'monthly': return timedelta(days=30)
    return timedelta(days=99999) # Default for 'all'

# --- Statistics Functions ---
def log_message(user_id, guild_id):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO messages (user_id, guild_id, timestamp) VALUES (?, ?, ?)", (user_id, guild_id, datetime.utcnow()))

def log_voice_session(user_id, guild_id, start_time, end_time):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO voice_sessions (user_id, guild_id, session_start, session_end) VALUES (?, ?, ?, ?)", (user_id, guild_id, start_time, end_time))

def get_message_stats(guild_id, period='all'):
    with get_db_connection() as conn:
        query = "SELECT user_id, COUNT(*) as message_count FROM messages WHERE guild_id = ? AND timestamp >= ? GROUP BY user_id ORDER BY message_count DESC"
        return conn.execute(query, (guild_id, datetime.utcnow() - _get_timedelta(period))).fetchall()

def get_voice_stats(guild_id, period='all'):
    with get_db_connection() as conn:
        query = "SELECT user_id, SUM(strftime('%s', session_end) - strftime('%s', session_start)) as total_seconds FROM voice_sessions WHERE guild_id = ? AND session_start >= ? GROUP BY user_id ORDER BY total_seconds DESC"
        return conn.execute(query, (guild_id, datetime.utcnow() - _get_timedelta(period))).fetchall()

def log_member_count(guild_id, member_count):
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO member_counts (guild_id, member_count, date) VALUES (?, ?, ?)", (guild_id, member_count, datetime.utcnow().date()))

def get_member_count_history(guild_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT date, member_count FROM member_counts WHERE guild_id = ? ORDER BY date ASC", (guild_id,)).fetchall()

def get_top_active_users(guild_id, limit=10):
    with get_db_connection() as conn:
        query = """
            SELECT user_id, SUM(message_score) + SUM(voice_score) AS combined_score FROM (
                SELECT user_id, COUNT(*) * 1.0 AS message_score, 0 AS voice_score FROM messages WHERE guild_id = ? GROUP BY user_id
                UNION ALL
                SELECT user_id, 0 AS message_score, SUM(strftime('%s', session_end) - strftime('%s', session_start)) / 10.0 AS voice_score FROM voice_sessions WHERE guild_id = ? GROUP BY user_id
            ) GROUP BY user_id ORDER BY combined_score DESC LIMIT ?"""
        return conn.execute(query, (guild_id, guild_id, limit)).fetchall()

# --- Guild Settings Functions ---
def get_guild_settings(guild_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        return conn.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)).fetchone()

def set_audit_log_channel(guild_id, channel_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE guild_settings SET audit_log_channel_id = ? WHERE guild_id = ?", (channel_id, guild_id))

# --- Auto-Responder Functions ---
def get_ar_config(guild_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO ar_settings (guild_id) VALUES (?)", (guild_id,))
        return conn.execute("SELECT * FROM ar_settings WHERE guild_id = ?", (guild_id,)).fetchone()

def get_ar_keywords(guild_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT keyword_type, keyword FROM ar_keywords WHERE guild_id = ?", (guild_id,)).fetchall()

def set_ar_enabled(guild_id, is_enabled):
    with get_db_connection() as conn:
        conn.execute("UPDATE ar_settings SET is_enabled = ? WHERE guild_id = ?", (int(is_enabled), guild_id))

def set_ar_channel(guild_id, channel_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE ar_settings SET target_channel_id = ? WHERE guild_id = ?", (channel_id, guild_id))

def set_ar_message(guild_id, message):
    with get_db_connection() as conn:
        conn.execute("UPDATE ar_settings SET reply_message = ? WHERE guild_id = ?", (message, guild_id))

def add_ar_keyword(guild_id, keyword_type, keyword):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, ?, ?)", (guild_id, keyword_type, keyword.lower()))
        return True
    except sqlite3.IntegrityError:
        return False

def remove_ar_keyword(guild_id, keyword_type, keyword):
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM ar_keywords WHERE guild_id = ? AND keyword_type = ? AND keyword = ?", (guild_id, keyword_type, keyword.lower()))
        return cursor.rowcount > 0

def seed_default_ar_keywords(guild_id):
    DEFAULT_TOPIC = ['celownik', 'czułość', 'dpi', 'myszka', 'grafika', 'ustawienia graficzne', 'rozdziałka', 'rozdzielczość', 'stretch', 'stretched', 'rozciągnięta', 'config', 'cfg', 'resolution', 'crosshair', 'sensitivity', 'sens']
    DEFAULT_QUESTION = ['jak', 'gdzie', 'ktoś', 'ma ktoś', 'poda', 'podeśle', 'podeślesz', 'jaki', 'jaka', 'jakie', 'czy', 'pomocy', 'pytanie', 'pomoże', 'macie', 'ustawić', 'zmienić', 'polecacie']
    with get_db_connection() as conn:
        c = conn.cursor()
        c.executemany("INSERT OR IGNORE INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, 'topic', ?)", [(guild_id, k) for k in DEFAULT_TOPIC])
        c.executemany("INSERT OR IGNORE INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, 'question', ?)", [(guild_id, k) for k in DEFAULT_QUESTION])
        return c.rowcount

# --- Warning System Functions ---
def get_warn_settings(guild_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO warn_settings (guild_id) VALUES (?)", (guild_id,))
        return conn.execute("SELECT * FROM warn_settings WHERE guild_id = ?", (guild_id,)).fetchone()

def set_warn_limit(guild_id, limit):
    with get_db_connection() as conn:
        conn.execute("UPDATE warn_settings SET warn_limit = ? WHERE guild_id = ?", (limit, guild_id))

def set_warn_action(guild_id, action):
    with get_db_connection() as conn:
        conn.execute("UPDATE warn_settings SET action = ? WHERE guild_id = ?", (action, guild_id))

def set_ban_duration(guild_id, duration_days):
    with get_db_connection() as conn:
        conn.execute("UPDATE warn_settings SET ban_duration_days = ? WHERE guild_id = ?", (duration_days, guild_id))

def add_warning(guild_id, user_id, moderator_id, reason):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)", (guild_id, user_id, moderator_id, reason, datetime.utcnow()))
        count = conn.execute("SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()[0]
        return count

def get_user_warnings(guild_id, user_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT warn_id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC", (guild_id, user_id)).fetchall()

def get_all_warnings_summary(guild_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT user_id, COUNT(*) as warn_count FROM warnings WHERE guild_id = ? GROUP BY user_id ORDER BY warn_count DESC", (guild_id,)).fetchall()

def remove_warning(warn_id, guild_id):
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM warnings WHERE warn_id = ? AND guild_id = ?", (warn_id, guild_id))
        return cursor.rowcount > 0

# --- Timed Ban Functions ---
def add_active_ban(guild_id, user_id, unban_timestamp):
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO active_bans (guild_id, user_id, unban_timestamp) VALUES (?, ?, ?)", (guild_id, user_id, unban_timestamp))

def get_expired_bans():
    with get_db_connection() as conn:
        return conn.execute("SELECT guild_id, user_id FROM active_bans WHERE unban_timestamp <= ?", (datetime.utcnow(),)).fetchall()

def remove_active_ban(guild_id, user_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM active_bans WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))

# --- Economy System Functions ---
def get_economy_settings(guild_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO economy_settings (guild_id) VALUES (?)", (guild_id,))
        return conn.execute("SELECT * FROM economy_settings WHERE guild_id = ?", (guild_id,)).fetchone()

def set_bet_win_chance(guild_id, chance):
    with get_db_connection() as conn:
        conn.execute("UPDATE economy_settings SET bet_win_chance = ? WHERE guild_id = ?", (chance, guild_id))

def get_wallet_balance(guild_id, user_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO economy_wallets (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        return conn.execute("SELECT balance FROM economy_wallets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()['balance']

def update_wallet_balance(guild_id, user_id, amount):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO economy_wallets (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.execute("UPDATE economy_wallets SET balance = balance + ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, user_id))
        return conn.execute("SELECT balance FROM economy_wallets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()['balance']

def get_top_balances(guild_id, limit=10):
    with get_db_connection() as conn:
        return conn.execute("SELECT user_id, balance FROM economy_wallets WHERE guild_id = ? ORDER BY balance DESC LIMIT ?", (guild_id, limit)).fetchall()

def get_shop_items(guild_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT item_id, role_id, price FROM economy_shop_items WHERE guild_id = ? ORDER BY price ASC", (guild_id,)).fetchall()

def get_shop_item(item_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM economy_shop_items WHERE item_id = ?", (item_id,)).fetchone()

def add_shop_item(guild_id, role_id, price):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO economy_shop_items (guild_id, role_id, price) VALUES (?, ?, ?)", (guild_id, role_id, price))
        return True
    except sqlite3.IntegrityError:
        return False

def remove_shop_item(item_id):
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM economy_shop_items WHERE item_id = ?", (item_id,))
        return cursor.rowcount > 0

def get_activity_scores_since(guild_id, since_timestamp):
    with get_db_connection() as conn:
        query = """
            SELECT user_id, SUM(message_score) + SUM(voice_score) AS activity_score FROM (
                SELECT user_id, COUNT(*) * 1.0 AS message_score, 0 AS voice_score FROM messages WHERE guild_id = ? AND timestamp > ? GROUP BY user_id
                UNION ALL
                SELECT user_id, 0 AS message_score, SUM(strftime('%s', session_end) - strftime('%s', session_start)) / 60.0 AS voice_score FROM voice_sessions WHERE guild_id = ? AND session_start > ? GROUP BY user_id
            ) GROUP BY user_id HAVING activity_score > 0"""
        return conn.execute(query, (guild_id, since_timestamp, guild_id, since_timestamp)).fetchall()