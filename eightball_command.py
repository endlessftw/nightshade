import random
import discord
from discord.ext import commands
from discord import app_commands

RESPONSES = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes — definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
]


class EightBall(commands.Cog):
    """Simple Magic 8-Ball implementation as a slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="What would you like to ask the 8-ball?")
    async def eightball(self, interaction: discord.Interaction, question: str):
        """Respond publicly with who asked, the question, and a random 8-ball answer."""
        asker = interaction.user.display_name
        answer = random.choice(RESPONSES)
        # Format exactly as requested: e.g. Emma asks: Should I eat"
        # Then a blank line and the 8ball answer prefixed by the emoji
        # Bold the asker name, the word 'asks', and the '8ball' label per user's request
        content = f"**{asker}** asks:** {question}\n\n **<a:8ball:1424657451038539806> 8ball: {answer}"
        # Send visibly in the channel
        await interaction.response.send_message(content, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(EightBall(bot))
