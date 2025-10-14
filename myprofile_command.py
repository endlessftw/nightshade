import discord
import logging
from discord.ext import commands
from discord import app_commands
from typing import Optional


class MyProfile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="myprofile", description="Show your userphone profile stats.")
    async def myprofile(self, interaction: discord.Interaction):
        user = interaction.user
        # Fetch stats from database
        db = getattr(self.bot, 'db', None)
        if db:
            try:
                stats = await db.get_user_stats(user.id)
                message_count = stats.get('userphone_messages', 0)
                started_count = stats.get('userphone_started', 0)
                ttt_wins = stats.get('wins_tictactoe', 0)
                c4_wins = stats.get('wins_connectfour', 0)
                rps_wins = stats.get('wins_rps', 0)
                hangman_wins = stats.get('wins_hangman', 0)
            except Exception as e:
                print(f"Failed to fetch stats from database: {e}")
                message_count = started_count = ttt_wins = c4_wins = rps_wins = hangman_wins = 0
        else:
            message_count = started_count = ttt_wins = c4_wins = rps_wins = hangman_wins = 0
        
        embed = discord.Embed(title="Userphone Profile", color=discord.Color.blue())
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Username", value=user.name, inline=False)
        embed.add_field(name="<a:phone:1424654842491834449> Total Userphone Messages", value=str(message_count), inline=False)
        embed.add_field(name="<a:phone:1424654842491834449> Total Userphones Started", value=str(started_count), inline=False)
        embed.add_field(name="<a:tictactoe:1424942287070433342> Tic-Tac-Toe Wins", value=str(ttt_wins), inline=False)
        embed.add_field(name="<a:connectfour:1425036938984947712> Connect Four Wins", value=str(c4_wins), inline=False)
        embed.add_field(name="<a:rockpaperscissor:1425347479389470720> Rock-Paper-Scissors Wins", value=str(rps_wins), inline=False)
        embed.add_field(name="🎮 Hangman Wins", value=str(hangman_wins), inline=False)

        # Try to send via interaction response; if the interaction is expired or unknown,
        # fall back to followup or DM the user to avoid raising NotFound.
        logger = logging.getLogger('myprofile')

        try:
            # Prefer to send the primary response if possible
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            except discord.NotFound as e:
                # Unknown interaction — try followup
                logger.debug('interaction.response.send_message NotFound, trying followup: %s', e)
            except discord.HTTPException as e:
                # Other HTTP problems when sending the response
                logger.debug('interaction.response.send_message HTTPException: %s', e)

            # If we reach here, try sending a followup message
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            except Exception as e:
                logger.debug('interaction.followup failed: %s', e)

            # Last resort: DM the user
            try:
                await interaction.user.send(embed=embed)
                return
            except Exception as e:
                logger.debug('DM to user failed: %s', e)

        except Exception as exc:
            # Catch-all to ensure we don't let an exception bubble up to app_commands
            logger.exception('Unhandled error when sending myprofile response: %s', exc)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(MyProfile(bot))
