import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


class UnwarnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings_file = os.path.join(os.path.dirname(__file__), 'warnings.json')
    
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
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        # Load current warnings
        warnings = self.load_warnings()
        
        # Check if user has any warnings
        if guild_id not in warnings or user_id not in warnings[guild_id] or not warnings[guild_id][user_id]:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> **{user}** has no warnings in this server.",
                ephemeral=True
            )
            return
        
        # Find the warning with the specified ID
        warning_to_remove = None
        warning_index = None
        
        for idx, warning in enumerate(warnings[guild_id][user_id]):
            if warning['warning_id'] == warning_id:
                warning_to_remove = warning
                warning_index = idx
                break
        
        if warning_to_remove is None:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Warning #{warning_id} not found for **{user}**.",
                ephemeral=True
            )
            return
        
        try:
            # Remove the warning
            warnings[guild_id][user_id].pop(warning_index)
            
            # If user has no more warnings, remove the user entry
            if not warnings[guild_id][user_id]:
                del warnings[guild_id][user_id]
            
            # If guild has no more warnings, remove the guild entry
            if not warnings[guild_id]:
                del warnings[guild_id]
            
            # Save warnings
            self.save_warnings(warnings)
            
            # Get remaining warnings count
            remaining_warnings = len(warnings.get(guild_id, {}).get(user_id, []))
            
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
            embed.add_field(name="Original Reason", value=warning_to_remove['reason'], inline=False)
            embed.add_field(name="Originally Given By", value=warning_to_remove['moderator_name'], inline=True)
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
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        # Load current warnings
        warnings = self.load_warnings()
        
        # Check if user has any warnings
        if guild_id not in warnings or user_id not in warnings[guild_id] or not warnings[guild_id][user_id]:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> **{user}** has no warnings in this server.",
                ephemeral=True
            )
            return
        
        try:
            # Get warning count before clearing
            warning_count = len(warnings[guild_id][user_id])
            
            # Clear all warnings for the user
            del warnings[guild_id][user_id]
            
            # If guild has no more warnings, remove the guild entry
            if not warnings[guild_id]:
                del warnings[guild_id]
            
            # Save warnings
            self.save_warnings(warnings)
            
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
    
    def load_warnings(self):
        """Load warnings from file"""
        try:
            if os.path.isfile(self.warnings_file):
                with open(self.warnings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[unwarn] Error loading warnings: {e}")
        return {}
    
    def save_warnings(self, warnings):
        """Save warnings to file"""
        try:
            with open(self.warnings_file, 'w') as f:
                json.dump(warnings, f, indent=2)
        except Exception as e:
            print(f"[unwarn] Error saving warnings: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UnwarnCog(bot))
