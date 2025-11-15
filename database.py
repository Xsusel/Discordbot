import sqlite3
from datetime import datetime

DB_NAME = 'bot_stats.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for guild-specific settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            currency_name TEXT NOT NULL DEFAULT 'Punkty',
            bet_win_chance INTEGER NOT NULL DEFAULT 45,
            shop_enabled INTEGER NOT NULL DEFAULT 1
        )
    ''')

    # Unified table for user statistics and points
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            activity_points INTEGER NOT NULL DEFAULT 0,
            monthly_activity_points INTEGER NOT NULL DEFAULT 0,
            gambling_points INTEGER NOT NULL DEFAULT 0,
            message_count INTEGER NOT NULL DEFAULT 0,
            voice_seconds INTEGER NOT NULL DEFAULT 0,
            last_activity_timestamp TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    ''')

    # Table for shop items (roles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            UNIQUE(guild_id, role_id)
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

# --- User Data Functions ---

def add_points(guild_id, user_id, activity_points_to_add, gambling_points_to_add):
    """Adds points for a user, creating a record if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id)
    )
    cursor.execute(
        """
        UPDATE users
        SET activity_points = activity_points + ?,
            monthly_activity_points = monthly_activity_points + ?,
            gambling_points = gambling_points + ?,
            last_activity_timestamp = ?
        WHERE guild_id = ? AND user_id = ?
        """,
        (activity_points_to_add, activity_points_to_add, gambling_points_to_add, datetime.utcnow(), guild_id, user_id)
    )
    conn.commit()
    conn.close()

def get_user_data(guild_id, user_id):
    """Gets all data for a user, creating a record if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id)
    )
    cursor.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def update_gambling_points(guild_id, user_id, amount):
    """Updates a user's gambling points by a relative amount."""
    get_user_data(guild_id, user_id) # Ensure user exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET gambling_points = gambling_points + ? WHERE guild_id = ? AND user_id = ?",
        (amount, guild_id, user_id)
    )
    conn.commit()
    cursor.execute("SELECT gambling_points FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    new_balance = cursor.fetchone()['gambling_points']
    conn.close()
    return new_balance

def get_leaderboard(guild_id, point_type='activity_points', limit=10):
    """Gets the top users based on a specified point type."""
    if point_type not in ['activity_points', 'gambling_points', 'monthly_activity_points']:
        raise ValueError("Invalid point_type specified.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT user_id, {point_type} FROM users WHERE guild_id = ? ORDER BY {point_type} DESC LIMIT ?",
        (guild_id, limit)
    )
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def reset_monthly_points(guild_id):
    """Resets the monthly activity points for all users in a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET monthly_activity_points = 0 WHERE guild_id = ?", (guild_id,))
    conn.commit()
    conn.close()

# --- Shop Functions ---

def add_shop_item(guild_id, role_id, price):
    """Adds a new item to the shop."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO shop_items (guild_id, role_id, price) VALUES (?, ?, ?)",
            (guild_id, role_id, price)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_shop_item(item_id):
    """Removes an item from the shop."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shop_items WHERE item_id = ?", (item_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

def get_shop_items(guild_id):
    """Gets all shop items for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, role_id, price FROM shop_items WHERE guild_id = ? ORDER BY price ASC", (guild_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_shop_item(item_id):
    """Gets a specific shop item by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shop_items WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item

# --- Guild Settings Functions ---

def get_guild_settings(guild_id):
    """Gets settings for a guild, creating a record if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
    cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
    settings = cursor.fetchone()
    conn.close()
    return settings

def set_bet_win_chance(guild_id, chance):
    """Sets the win chance for the betting game."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guild_settings SET bet_win_chance = ? WHERE guild_id = ?", (chance, guild_id))
    conn.commit()
    conn.close()
