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
        # read stats from bot attributes set in main.py
        message_count = getattr(self.bot, 'userphone_message_count', {}).get(user.id, 0)
        started_count = getattr(self.bot, 'userphone_started_count', {}).get(user.id, 0)
        embed = discord.Embed(title="Userphone Profile", color=discord.Color.blue())
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Username", value=user.name, inline=False)
        embed.add_field(name="<a:phone:1424654842491834449> Total Userphone Messages", value=str(message_count), inline=False)
        embed.add_field(name="<a:phone:1424654842491834449> Total Userphones Started", value=str(started_count), inline=False)
        # include wins from games if available
        ttt_wins = getattr(self.bot, 'user_wins_tictactoe', {}).get(user.id, 0)
        c4_wins = getattr(self.bot, 'user_wins_connectfour', {}).get(user.id, 0)
        rps_wins = getattr(self.bot, 'user_wins_rps', {}).get(user.id, 0)
        hangman_wins = getattr(self.bot, 'user_wins_hangman', {}).get(user.id, 0)
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
