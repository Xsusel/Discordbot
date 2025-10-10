import discord
from discord.ext import commands
import os
import google.generativeai as genai

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            print("Gemini AI cog loaded and configured.")
        else:
            self.model = None
            print("Gemini API key not found. AI cog will be disabled.")

    async def get_ai_response(self, message_content: str):
        if not self.model:
            return None

        try:
            response = self.model.generate_content(message_content)
            return response.text
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "Sorry, I encountered an error while processing your request."

async def setup(bot):
    await bot.add_cog(AI(bot))