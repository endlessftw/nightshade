import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime


class BanCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='ban', description='Ban a user from the server')
    @app_commands.describe(
        user='The user to ban (can be a member or user ID)',
        reason='Reason for the ban (optional)',
        delete_message_days='Delete messages from the last X days (0-7, default: 0)'
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self, 
        interaction: discord.Interaction, 
        user: discord.User,  # Changed from discord.Member to discord.User to allow banning non-members
        reason: str = "No reason provided",
        delete_message_days: int = 0
    ):
        # Check if bot has permission
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to ban members!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to ban themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot ban yourself!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to ban the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot ban myself!",
                ephemeral=True
            )
            return
        
        # Check if target user is the server owner
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot ban the server owner!",
                ephemeral=True
            )
            return
        
        # Check role hierarchy (only if user is a member of the server)
        member = interaction.guild.get_member(user.id)
        if member:  # User is in the server, check role hierarchy
            if interaction.user.id != interaction.guild.owner_id:  # Owner can ban anyone
                if member.top_role >= interaction.user.top_role:
                    await interaction.response.send_message(
                        "<a:warning:1424944783587147868> You cannot ban someone with an equal or higher role!",
                        ephemeral=True
                    )
                    return
            
            # Check if bot can ban this user (role hierarchy)
            if member.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> I cannot ban someone with an equal or higher role than me!",
                    ephemeral=True
                )
                return
        
        # Validate delete_message_days
        if delete_message_days < 0 or delete_message_days > 7:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Delete message days must be between 0 and 7!",
                ephemeral=True
            )
            return
        
        try:
            # Try to DM the user before banning
            try:
                dm_embed = discord.Embed(
                    title="<:banhammer:1426111097005539371> You have been banned",
                    description=f"You have been banned from **{interaction.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Ban the user
            await interaction.guild.ban(
                user, 
                reason=f"Banned by {interaction.user} ({interaction.user.id}) - {reason}",
                delete_message_days=delete_message_days
            )
            
            # Send success message
            embed = discord.Embed(
                title="<:banhammer:1426111097005539371> User Banned",
                description=f"**{user}** (`{user.id}`) has been banned from the server.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Messages Deleted", value=f"Last {delete_message_days} day(s)", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the ban (if you have a logging channel)
            # You can add logging functionality here
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to ban this user!",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Failed to ban user: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You need 'Ban Members' permission to use this command!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {error}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(BanCog(bot))
