import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional


class PurgeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete a specified number of messages from the channel.")
    @app_commands.describe(amount="The number of messages to delete (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        """Delete multiple messages from a channel"""
        
        # Validate the amount
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Please specify a number between 1 and 100.",
                ephemeral=True
            )
            return
        
        # Defer the response since purging might take a moment
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Delete the messages (this doesn't include the command interaction itself)
            deleted = await interaction.channel.purge(limit=amount)
            
            # Send confirmation message
            await interaction.followup.send(
                f"<a:purge:1431407576540512348> Successfully deleted {len(deleted)} message(s).",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "<a:warning:1424944783587147868> I don't have permission to delete messages in this channel.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"<a:warning:1424944783587147868> Failed to delete messages: {e}",
                ephemeral=True
            )
    
    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the purge command"""
        if isinstance(error, app_commands.errors.MissingPermissions):
            try:
                # Check if interaction was already responded to
                if interaction.response.is_done():
                    await interaction.followup.send(
                        "<a:warning:1424944783587147868> You don't have permission to use this command. You need the `Manage Messages` permission.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "<a:warning:1424944783587147868> You don't have permission to use this command. You need the `Manage Messages` permission.",
                        ephemeral=True
                    )
            except:
                # Silently fail if we can't send the error message
                pass
        else:
            # Log the error but don't try to send a message
            print(f"[purge_error] Error occurred: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(PurgeCog(bot))
