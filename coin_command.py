import os
import io
import random
import discord
from discord.ext import commands
from discord import app_commands


class CoinCog(commands.Cog):
    """Simple coin flip command that shows an image for heads or tails."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Preload coin images into memory (bytes) to avoid disk I/O on each command
        self.image_cache = {}
        for name in ("nighthead.png", "nighttails.png"):
            path = os.path.join(os.path.dirname(__file__), name)
            try:
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        self.image_cache[name] = f.read()
            except Exception:
                # ignore preload errors; fallback will use emoji
                self.image_cache[name] = None

    @app_commands.command(name="coin", description="Flip a coin (50/50) and show heads or tails.")
    async def coin(self, interaction: discord.Interaction):
        # Defer immediately to acknowledge the interaction so we can upload attachments
        # and send the final message via followup without hitting the 3-second window.
        await interaction.response.defer(ephemeral=False)

        outcome = "Heads" if random.choice([True, False]) else "Tails"
        img_name = "nighthead.png" if outcome == "Heads" else "nighttails.png"

        embed = discord.Embed(title=f"<a:coin:1424668396573691906> Your coin landed on {outcome}", color=discord.Color.blurple())

        img_bytes = self.image_cache.get(img_name)
        if img_bytes:
            file = discord.File(io.BytesIO(img_bytes), filename=img_name)
            embed.set_image(url=f"attachment://{img_name}")
            await interaction.followup.send(file=file, embed=embed)
            return

        # Fallback: try file on disk, then emoji
        img_path = os.path.join(os.path.dirname(__file__), img_name)
        if os.path.isfile(img_path):
            file = discord.File(img_path, filename=img_name)
            embed.set_image(url=f"attachment://{img_name}")
            await interaction.followup.send(file=file, embed=embed)
            return

        emoji = "🪙" if outcome == "Heads" else "🎲"
        embed.description = emoji
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CoinCog(bot))
