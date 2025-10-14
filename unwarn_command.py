import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


class UnwarnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = getattr(bot, 'db', None)
    
    @app_commands.command(name='unwarn', description='Remove a warning from a user')
    @app_commands.describe(
        user='The user to remove a warning from',
        warning_id='The warning ID to remove (use /warnings to see IDs)'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unwarn(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        warning_id: int
    ):
        if not self.db:
            await interaction.response.send_message(
                "❌ Database not available.",
                ephemeral=True
            )
            return
        
        # Check if warning exists
        warnings_list = await self.db.get_warnings(interaction.guild.id, user.id)
        
        if not warnings_list:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> **{user}** has no warnings in this server.",
                ephemeral=True
            )
            return
        
        # Find the warning
        warning_to_remove = None
        for warning in warnings_list:
            if warning['id'] == warning_id:
                warning_to_remove = warning
                break
        
        if not warning_to_remove:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Warning #{warning_id} not found for **{user}**.",
                ephemeral=True
            )
            return
        
        try:
            # Remove the warning from database
            removed = await self.db.remove_warning(warning_id, interaction.guild.id)
            
            if not removed:
                await interaction.response.send_message(
                    f"<a:warning:1424944783587147868> Failed to remove warning #{warning_id}.",
                    ephemeral=True
                )
                return
            
            # Get remaining warnings count
            remaining_warnings_list = await self.db.get_warnings(interaction.guild.id, user.id)
            remaining_warnings = len(remaining_warnings_list)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="✅ Warning Removed",
                    description=f"One of your warnings in **{interaction.guild.name}** has been removed.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                dm_embed.add_field(name="Warning ID", value=f"#{warning_id}", inline=False)
                dm_embed.add_field(name="Removed by", value=interaction.user.mention, inline=False)
                dm_embed.add_field(name="Remaining Warnings", value=str(remaining_warnings), inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Send success message
            embed = discord.Embed(
                title="✅ Warning Removed",
                description=f"Warning #{warning_id} has been removed from **{user}** (`{user.id}`).",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            # Get moderator mention
            moderator = interaction.guild.get_member(warning_to_remove['moderator_id'])
            moderator_text = moderator.mention if moderator else f"<@{warning_to_remove['moderator_id']}>"
            
            embed.add_field(name="Original Reason", value=warning_to_remove['reason'], inline=False)
            embed.add_field(name="Originally Given By", value=moderator_text, inline=True)
            embed.add_field(name="Removed By", value=interaction.user.mention, inline=True)
            embed.add_field(name="Remaining Warnings", value=str(remaining_warnings), inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name='clearwarnings', description='Clear all warnings for a user')
    @app_commands.describe(
        user='The user to clear all warnings from'
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarnings(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member
    ):
        if not self.db:
            await interaction.response.send_message(
                "❌ Database not available.",
                ephemeral=True
            )
            return
        
        # Check if user has any warnings
        warnings_list = await self.db.get_warnings(interaction.guild.id, user.id)
        
        if not warnings_list:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> **{user}** has no warnings in this server.",
                ephemeral=True
            )
            return
        
        try:
            # Get warning count before clearing
            warning_count = len(warnings_list)
            
            # Clear all warnings for the user
            cleared_count = await self.db.clear_warnings(interaction.guild.id, user.id)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="✅ All Warnings Cleared",
                    description=f"All your warnings in **{interaction.guild.name}** have been cleared.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                dm_embed.add_field(name="Warnings Cleared", value=str(warning_count), inline=False)
                dm_embed.add_field(name="Cleared by", value=interaction.user.mention, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Send success message
            embed = discord.Embed(
                title="✅ All Warnings Cleared",
                description=f"All warnings have been cleared from **{user}** (`{user.id}`).",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Warnings Cleared", value=str(warning_count), inline=True)
            embed.add_field(name="Cleared By", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @unwarn.error
    async def unwarn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You need 'Moderate Members' permission to use this command!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {error}",
                ephemeral=True
            )
    
    @clearwarnings.error
    async def clearwarnings_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You need 'Administrator' permission to use this command!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {error}",
                ephemeral=True
            )
    
    # Database methods - no longer needed, handled by database.py


async def setup(bot: commands.Bot):
    await bot.add_cog(UnwarnCog(bot))
