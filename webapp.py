import os
import discord
import database
from flask import Flask, render_template, abort
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)

bot_client = None

def set_bot_client(client):
    """A function to pass the bot client to the web app."""
    global bot_client
    bot_client = client

def generate_member_chart(history, guild_name):
    """Generates a line chart of member count history and returns it as a base64 string."""
    if not history:
        return None

    dates = [row['date'] for row in history]
    counts = [row['member_count'] for row in history]

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(dates, counts, marker='o', linestyle='-', color='cyan')

    ax.set_title(f'Member Count Over Time for {guild_name}', color='white', fontsize=16)
    ax.set_xlabel('Date', color='white', fontsize=12)
    ax.set_ylabel('Member Count', color='white', fontsize=12)

    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
    ax.tick_params(axis='x', colors='white', rotation=45)
    ax.tick_params(axis='y', colors='white')

    for spine in ax.spines.values():
        spine.set_edgecolor('gray')

    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    return chart_base64

@app.route('/dashboard/<int:guild_id>')
def dashboard(guild_id):
    """The main dashboard page for a specific guild."""
    try:
        if not bot_client or not bot_client.is_ready():
            abort(503, "Bot client not initialized or not ready.")

        guild = bot_client.get_guild(guild_id)
        if not guild:
            abort(404, "Guild not found.")

        # Get member count history and generate chart
        history = database.get_member_count_history(guild_id)
        chart = generate_member_chart(history, guild.name)

        # Get top 10 active users from the new leaderboard function
        top_users_data = database.get_leaderboard(guild_id, point_type='activity_points', limit=10)
        top_users = []
        for user_row in top_users_data:
            member = guild.get_member(user_row['user_id'])
            if member:
                display_name = member.display_name
                avatar_url = member.avatar.url if member.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
            else:
                display_name = f"Unknown User (ID: {user_row['user_id']})"
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"

            top_users.append({
                'name': display_name,
                'avatar_url': avatar_url,
                'score': user_row['activity_points']
            })

        return render_template('index.html',
                               guild_name=guild.name,
                               member_chart=chart,
                               top_users=top_users)
    except Exception as e:
        import traceback
        print(f"!!! An error occurred while generating the dashboard for guild {guild_id} !!!")
        traceback.print_exc()
        abort(500, f"An internal error occurred: {e}")

def run_webapp():
    """Runs the Flask web application."""
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    run_webapp()
