import sqlite3
from datetime import datetime, timedelta

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

    # Table for general guild settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            audit_log_channel_id INTEGER
        )
    ''')

    # Table for auto-responder settings per guild
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ar_settings (
            guild_id INTEGER PRIMARY KEY,
            is_enabled INTEGER NOT NULL DEFAULT 0,
            target_channel_id INTEGER,
            reply_message TEXT NOT NULL DEFAULT 'Cześć, {mention}! Widzę, że pytasz o ustawienia. Wszystkie potrzebne informacje znajdziesz na kanale <#{channel}>.'
        )
    ''')

    # Table for auto-responder keywords per guild
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ar_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            keyword_type TEXT NOT NULL, -- 'topic' or 'question'
            keyword TEXT NOT NULL,
            UNIQUE(guild_id, keyword_type, keyword)
        )
    ''')

    # Table for warning system settings per guild
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warn_settings (
            guild_id INTEGER PRIMARY KEY,
            warn_limit INTEGER NOT NULL DEFAULT 3,
            action TEXT NOT NULL DEFAULT 'kick', -- 'kick' or 'ban'
            ban_duration_days INTEGER DEFAULT 7
        )
    ''')

    # Table for individual warnings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT,
            timestamp TIMESTAMP NOT NULL
        )
    ''')

    # Table to track active timed bans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_bans (
            ban_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            unban_timestamp TIMESTAMP NOT NULL,
            UNIQUE(guild_id, user_id)
        )
    ''')

    # Table for economy system settings per guild
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economy_settings (
            guild_id INTEGER PRIMARY KEY,
            currency_name TEXT NOT NULL DEFAULT 'Points',
            bet_win_chance INTEGER NOT NULL DEFAULT 45 -- Percentage
        )
    ''')

    # Table for user wallets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economy_wallets (
            wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            UNIQUE(guild_id, user_id)
        )
    ''')

    # Table for shop items (roles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economy_shop_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            UNIQUE(guild_id, role_id)
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

# --- Auto-Responder Functions ---

def get_ar_config(guild_id):
    """Gets the auto-responder configuration for a specific guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO ar_settings (guild_id) VALUES (?)", (guild_id,))
    conn.commit()
    cursor.execute("SELECT * FROM ar_settings WHERE guild_id = ?", (guild_id,))
    config = cursor.fetchone()
    conn.close()
    return config

def get_ar_keywords(guild_id):
    """Gets all auto-responder keywords for a specific guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keyword_type, keyword FROM ar_keywords WHERE guild_id = ?", (guild_id,))
    keywords = cursor.fetchall()
    conn.close()
    return keywords

def set_ar_enabled(guild_id, is_enabled):
    """Enables or disables the auto-responder for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure a settings row exists before trying to update it
    cursor.execute("INSERT OR IGNORE INTO ar_settings (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("UPDATE ar_settings SET is_enabled = ? WHERE guild_id = ?", (int(is_enabled), guild_id))
    conn.commit()
    conn.close()

def set_ar_channel(guild_id, channel_id):
    """Sets the target channel for the auto-responder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure a settings row exists before trying to update it
    cursor.execute("INSERT OR IGNORE INTO ar_settings (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("UPDATE ar_settings SET target_channel_id = ? WHERE guild_id = ?", (channel_id, guild_id))
    conn.commit()
    conn.close()

def set_ar_message(guild_id, message):
    """Sets the custom reply message for the auto-responder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure a settings row exists before trying to update it
    cursor.execute("INSERT OR IGNORE INTO ar_settings (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("UPDATE ar_settings SET reply_message = ? WHERE guild_id = ?", (message, guild_id))
    conn.commit()
    conn.close()

def add_ar_keyword(guild_id, keyword_type, keyword):
    """Adds a keyword to the auto-responder list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, ?, ?)",
            (guild_id, keyword_type, keyword.lower())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # This keyword already exists
        return False
    finally:
        conn.close()

# --- Guild Settings Functions ---

def get_guild_settings(guild_id):
    """Gets all settings for a specific guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
    conn.commit()
    cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
    settings = cursor.fetchone()
    conn.close()
    return settings

def set_audit_log_channel(guild_id, channel_id):
    """Sets the audit log channel for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guild_settings SET audit_log_channel_id = ? WHERE guild_id = ?", (channel_id, guild_id))
    conn.commit()
    conn.close()

# --- Economy System Functions ---

def get_economy_settings(guild_id):
    """Gets the economy system configuration for a specific guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO economy_settings (guild_id) VALUES (?)", (guild_id,))
    conn.commit()
    cursor.execute("SELECT * FROM economy_settings WHERE guild_id = ?", (guild_id,))
    settings = cursor.fetchone()
    conn.close()
    return settings

def set_bet_win_chance(guild_id, chance):
    """Sets the win chance for the betting game."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE economy_settings SET bet_win_chance = ? WHERE guild_id = ?", (chance, guild_id))
    conn.commit()
    conn.close()

def get_wallet_balance(guild_id, user_id):
    """Gets the wallet balance for a user, creating a wallet if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO economy_wallets (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
    conn.commit()
    cursor.execute("SELECT balance FROM economy_wallets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result['balance'] if result else 0

def update_wallet_balance(guild_id, user_id, amount):
    """Updates a user's wallet balance by a relative amount (can be negative)."""
    # First, ensure the wallet exists
    get_wallet_balance(guild_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE economy_wallets SET balance = balance + ? WHERE guild_id = ? AND user_id = ?",
        (amount, guild_id, user_id)
    )
    conn.commit()
    # Fetch the new balance
    cursor.execute("SELECT balance FROM economy_wallets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    new_balance = cursor.fetchone()['balance']
    conn.close()
    return new_balance

def get_top_balances(guild_id, limit=10):
    """Gets the top N richest users in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, balance FROM economy_wallets WHERE guild_id = ? ORDER BY balance DESC LIMIT ?",
        (guild_id, limit)
    )
    top_users = cursor.fetchall()
    conn.close()
    return top_users

def get_shop_items(guild_id):
    """Gets all shop items for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, role_id, price FROM economy_shop_items WHERE guild_id = ? ORDER BY price ASC", (guild_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_shop_item(item_id):
    """Gets a specific shop item by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM economy_shop_items WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item

def add_shop_item(guild_id, role_id, price):
    """Adds a new item to the shop."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO economy_shop_items (guild_id, role_id, price) VALUES (?, ?, ?)",
            (guild_id, role_id, price)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Item (role) already exists
    finally:
        conn.close()

def remove_shop_item(item_id):
    """Removes an item from the shop."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM economy_shop_items WHERE item_id = ?", (item_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

def get_activity_scores_since(guild_id, since_timestamp):
    """Calculates activity scores for all users since a given timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            user_id,
            SUM(message_score) + SUM(voice_score) AS activity_score
        FROM (
            SELECT user_id, COUNT(*) * 1.0 AS message_score, 0 AS voice_score
            FROM messages
            WHERE guild_id = ? AND timestamp > ?
            GROUP BY user_id
            UNION ALL
            SELECT user_id, 0 AS message_score, SUM(strftime('%s', session_end) - strftime('%s', session_start)) / 60.0 AS voice_score
            FROM voice_sessions
            WHERE guild_id = ? AND session_start > ?
            GROUP BY user_id
        )
        GROUP BY user_id
        HAVING activity_score > 0
    """
    cursor.execute(query, (guild_id, since_timestamp, guild_id, since_timestamp))
    scores = cursor.fetchall()
    conn.close()
    return scores

def remove_ar_keyword(guild_id, keyword_type, keyword):
    """Removes a keyword from the auto-responder list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM ar_keywords WHERE guild_id = ? AND keyword_type = ? AND keyword = ?",
        (guild_id, keyword_type, keyword.lower())
    )
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

def add_active_ban(guild_id, user_id, unban_timestamp):
    """Adds a record for an active timed ban."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO active_bans (guild_id, user_id, unban_timestamp) VALUES (?, ?, ?)",
        (guild_id, user_id, unban_timestamp)
    )
    conn.commit()
    conn.close()

def get_expired_bans():
    """Retrieves all bans that are past their expiration timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()
    cursor.execute("SELECT guild_id, user_id FROM active_bans WHERE unban_timestamp <= ?", (now,))
    expired_bans = cursor.fetchall()
    conn.close()
    return expired_bans

def remove_active_ban(guild_id, user_id):
    """Removes an active ban record, typically after the user has been unbanned."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_bans WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    conn.commit()
    conn.close()

def seed_default_ar_keywords(guild_id):
    """Seeds the database with a default set of keywords for a guild."""
    DEFAULT_TOPIC_KEYWORDS = [
        'celownik', 'czułość', 'dpi', 'myszka', 'grafika', 'ustawienia graficzne',
        'rozdziałka', 'rozdzielczość', 'stretch', 'stretched', 'rozciągnięta',
        'config', 'cfg', 'resolution', 'crosshair', 'sensitivity', 'sens'
    ]
    DEFAULT_QUESTION_WORDS = [
        'jak', 'gdzie', 'ktoś', 'ma ktoś', 'poda', 'podeśle', 'podeślesz', 'jaki',
        'jaka', 'jakie', 'czy', 'pomocy', 'pytanie', 'pomoże', 'macie', 'ustawić',
        'zmienić', 'polecacie'
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    topic_inserts = [(guild_id, 'topic', keyword) for keyword in DEFAULT_TOPIC_KEYWORDS]
    question_inserts = [(guild_id, 'question', keyword) for keyword in DEFAULT_QUESTION_WORDS]

    try:
        # Use executemany for efficiency and IGNORE to skip duplicates
        cursor.executemany("INSERT OR IGNORE INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, ?, ?)", topic_inserts)
        cursor.executemany("INSERT OR IGNORE INTO ar_keywords (guild_id, keyword_type, keyword) VALUES (?, ?, ?)", question_inserts)
        conn.commit()
        return conn.total_changes
    except Exception as e:
        print(f"Error seeding keywords: {e}")
        return 0
    finally:
        conn.close()

# --- Warning System Functions ---

def get_warn_settings(guild_id):
    """Gets the warning system configuration for a specific guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO warn_settings (guild_id) VALUES (?)", (guild_id,))
    conn.commit()
    cursor.execute("SELECT * FROM warn_settings WHERE guild_id = ?", (guild_id,))
    settings = cursor.fetchone()
    conn.close()
    return settings

def set_warn_limit(guild_id, limit):
    """Sets the warning limit for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE warn_settings SET warn_limit = ? WHERE guild_id = ?", (limit, guild_id))
    conn.commit()
    conn.close()

def set_warn_action(guild_id, action):
    """Sets the enforcement action for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE warn_settings SET action = ? WHERE guild_id = ?", (action, guild_id))
    conn.commit()
    conn.close()

def set_ban_duration(guild_id, duration_days):
    """Sets the ban duration for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE warn_settings SET ban_duration_days = ? WHERE guild_id = ?", (duration_days, guild_id))
    conn.commit()
    conn.close()

def add_warning(guild_id, user_id, moderator_id, reason):
    """Adds a warning for a user and returns their new total warning count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, moderator_id, reason, datetime.utcnow())
    )
    conn.commit()

    # Get the new total number of warnings for the user
    cursor.execute("SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    count = cursor.fetchone()[0]

    conn.close()
    return count

def get_user_warnings(guild_id, user_id):
    """Retrieves all warnings for a specific user in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT warn_id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC", (guild_id, user_id))
    warnings = cursor.fetchall()
    conn.close()
    return warnings

def get_all_warnings_summary(guild_id):
    """Retrieves a summary of warning counts for all users in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, COUNT(*) as warn_count FROM warnings WHERE guild_id = ? GROUP BY user_id ORDER BY warn_count DESC", (guild_id,))
    summary = cursor.fetchall()
    conn.close()
    return summary

def remove_warning(warn_id, guild_id):
    """Removes a specific warning by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warnings WHERE warn_id = ? AND guild_id = ?", (warn_id, guild_id))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0