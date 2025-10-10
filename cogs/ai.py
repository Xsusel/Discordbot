import discord
from discord.ext import commands
import os
import google.generativeai as genai
import logging
import traceback

logger = logging.getLogger(__name__)

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = None
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                logger.info("Gemini AI cog loaded and configured with model 'gemini-1.5-flash-latest'.")

                # Log available models for debugging purposes
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                logger.info(f"Available Gemini models supporting 'generateContent': {models}")

            except Exception as e:
                logger.error(f"Failed to configure Gemini or list models: {e}")
                logger.error(traceback.format_exc())
                self.model = None
        else:
            logger.warning("Gemini API key not found or is set to the default placeholder. AI cog will be disabled.")

    async def get_ai_response(self, message_content: str):
        if not self.model:
            logger.warning("AI response requested, but model is not available.")
            return None

        try:
            logger.info(f"Sending prompt to Gemini: '{message_content}'")
            response = await self.model.generate_content_async(message_content)

            logger.info(f"Received raw response from Gemini: {response}")

            # The most reliable way to check for a blocked response is to inspect the prompt_feedback.
            if response.prompt_feedback.block_reason:
                logger.warning(f"Response blocked by safety filters. Reason: {response.prompt_feedback.block_reason.name}")
                return "I am sorry, but my safety filters prevent me from responding to that."

            # If the response was not blocked, it should have text content.
            return response.text
        except Exception as e:
            # Log the full traceback to get detailed error information
            logger.error(f"An unexpected error occurred while getting AI response: {e}")
            logger.error(traceback.format_exc())
            return "Sorry, I encountered an unexpected error while processing your request."

async def setup(bot):
    await bot.add_cog(AI(bot))