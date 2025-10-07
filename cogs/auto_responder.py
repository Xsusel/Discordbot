import discord
from discord.ext import commands
import os

# Expanded keyword lists for better detection
TOPIC_KEYWORDS = [
    'celownik', 'czułość', 'dpi', 'myszka', 'grafika',
    'ustawienia graficzne', 'rozdziałka', 'rozdzielczość',
    'stretch', 'stretched', 'rozciągnięta', 'config', 'cfg',
    'resolution', 'crosshair', 'sensitivity', 'sens'
]

QUESTION_WORDS = [
    'jak', 'gdzie', 'ktoś', 'ma ktoś', 'poda', 'podeśle', 'podeślesz',
    'jaki', 'jaka', 'jakie', 'czy', 'pomocy', 'pytanie', 'pomoże',
    'macie', 'ustawić', 'zmienić', 'polecacie'
]

class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.target_channel_id = int(os.getenv('SETTINGS_INFO_CHANNEL_ID'))
            print(f"Auto-responder loaded. Target channel ID: {self.target_channel_id}")
        except (TypeError, ValueError):
            self.target_channel_id = None
            print("WARNING: SETTINGS_INFO_CHANNEL_ID is not set or invalid. Auto-responder is disabled.")

    async def check_for_response(self, message):
        """Checks a message and sends an auto-response if it matches criteria."""
        # Ignore if the feature is disabled, if the message is from a bot, or if it's in the target channel
        if not self.target_channel_id or message.author.bot or message.channel.id == self.target_channel_id:
            return

        message_content_lower = message.content.lower()

        # Check if the message contains any of the relevant topic keywords
        has_topic_keyword = any(keyword in message_content_lower for keyword in TOPIC_KEYWORDS)

        if not has_topic_keyword:
            return

        # Check if the message is likely a question
        is_a_question = False
        if message_content_lower.endswith('?'):
            is_a_question = True
        if not is_a_question and any(q_word in message_content_lower.split() for q_word in QUESTION_WORDS):
            is_a_question = True

        if is_a_question:
            try:
                reply_message = (
                    f"Cześć, {message.author.mention}! Widzę, że pytasz o ustawienia.\n"
                    f"Wszystkie potrzebne informacje, takie jak configi, celowniki czy ustawienia 'true stretched', znajdziesz na kanale <#{self.target_channel_id}>."
                )
                await message.reply(reply_message, mention_author=False)
                print(f"Auto-responded to a settings question from {message.author}.")
            except discord.errors.Forbidden:
                print(f"Could not reply to {message.author} in channel {message.channel.id}. Missing permissions.")
            except Exception as e:
                print(f"An error occurred in auto-responder: {e}")

async def setup(bot):
    await bot.add_cog(AutoResponder(bot))