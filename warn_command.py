import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime


class WarnCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warnings_file = os.path.join(os.path.dirname(__file__), 'warnings.json')
        self.warnings = self.load_warnings()
    
    @app_commands.command(name='warn', description='Warn a user for breaking rules')
    @app_commands.describe(
        user='The user to warn',
        reason='Reason for the warning'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        reason: str
    ):
        # Check if bot has permission
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to manage warnings!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to warn themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot warn yourself!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to warn the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot warn me!",
                ephemeral=True
            )
            return
        
        # Check if target user is the server owner
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot warn the server owner!",
                ephemeral=True
            )
            return
        
        # Check role hierarchy
        if interaction.user.id != interaction.guild.owner_id:
            if user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> You cannot warn someone with an equal or higher role!",
                    ephemeral=True
                )
                return
        
        try:
            # Create warning entry
            guild_id = str(interaction.guild.id)
            user_id = str(user.id)
            
            # Initialize guild warnings if needed
            if guild_id not in self.warnings:
                self.warnings[guild_id] = {}
            
            # Initialize user warnings if needed
            if user_id not in self.warnings[guild_id]:
                self.warnings[guild_id][user_id] = []
            
            # Add warning
            warning = {
                'reason': reason,
                'moderator_id': interaction.user.id,
                'moderator_name': str(interaction.user),
                'timestamp': datetime.utcnow().isoformat(),
                'warning_id': len(self.warnings[guild_id][user_id]) + 1
            }
            
            self.warnings[guild_id][user_id].append(warning)
            self.save_warnings()
            
            # Get total warnings
            total_warnings = len(self.warnings[guild_id][user_id])
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="<a:warn:1426420218518835263> You have been warned",
                    description=f"You have received a warning in **{interaction.guild.name}**",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                dm_embed.add_field(name="Total Warnings", value=str(total_warnings), inline=False)
                dm_embed.set_footer(text="Please follow the server rules to avoid further action.")
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Send success message
            embed = discord.Embed(
                title="<a:warn:1426420218518835263> User Warned",
                description=f"**{user}** (`{user.id}`) has been warned.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Total Warnings", value=str(total_warnings), inline=True)
            embed.add_field(name="Warning ID", value=f"#{warning['warning_id']}", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name='warnings', description='View all warnings for a user')
    @app_commands.describe(
        user='The user to check warnings for'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member
    ):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        
        # Check if user has any warnings
        if guild_id not in self.warnings or user_id not in self.warnings[guild_id] or not self.warnings[guild_id][user_id]:
            await interaction.response.send_message(
                f"✅ **{user}** has no warnings in this server.",
                ephemeral=True
            )
            return
        
        # Create embed with all warnings
        embed = discord.Embed(
            title=f"<a:warn:1426420218518835263> Warnings for {user.name}",
            description=f"Total warnings: **{len(self.warnings[guild_id][user_id])}**",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Add each warning as a field
        for warning in self.warnings[guild_id][user_id]:
            timestamp = datetime.fromisoformat(warning['timestamp'])
            timestamp_unix = int(timestamp.timestamp())
            
            field_value = (
                f"**Reason:** {warning['reason']}\n"
                f"**Moderator:** {warning['moderator_name']}\n"
                f"**Date:** <t:{timestamp_unix}:F>"
            )
            
            embed.add_field(
                name=f"Warning #{warning['warning_id']}",
                value=field_value,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @warn.error
    async def warn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    
    @warnings.error
    async def warnings_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    
    def load_warnings(self):
        """Load warnings from file"""
        try:
            if os.path.isfile(self.warnings_file):
                with open(self.warnings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[warn] Error loading warnings: {e}")
        return {}
    
    def save_warnings(self):
        """Save warnings to file"""
        try:
            with open(self.warnings_file, 'w') as f:
                json.dump(self.warnings, f, indent=2)
        except Exception as e:
            print(f"[warn] Error saving warnings: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(WarnCog(bot))
