import discord
from discord.ext import commands
from discord import app_commands
import time

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Show the bot's latency and response time.")
    async def ping(self, interaction: discord.Interaction):
        # websocket latency
        ws_latency_ms = round(self.bot.latency * 1000)
        # measure round-trip by sending a public message then editing it
        start = time.perf_counter()
        # send a visible message in the channel (not ephemeral)
        await interaction.response.send_message(f"Pinging... (websocket {ws_latency_ms} ms)", ephemeral=False)
        rtt = round((time.perf_counter() - start) * 1000)
        try:
            await interaction.edit_original_response(content=f"<a:ping:1424656851173113937> Pong! WebSocket latency: {ws_latency_ms} ms • Response RTT: {rtt} ms")
        except Exception:
            # If edit fails, send a visible follow-up
            await interaction.followup.send(f"<a:ping:1424656851173113937> Pong! WebSocket latency: {ws_latency_ms} ms • Response RTT: {rtt} ms", ephemeral=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
