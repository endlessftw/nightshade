import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime


class KickCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='kick', description='Kick a user from the server')
    @app_commands.describe(
        user='The user to kick',
        reason='Reason for the kick (optional)'
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        reason: str = "No reason provided"
    ):
        # Check if bot has permission
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to kick members!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to kick themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot kick yourself!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to kick the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot kick myself!",
                ephemeral=True
            )
            return
        
        # Check if target user is the server owner
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot kick the server owner!",
                ephemeral=True
            )
            return
        
        # Check role hierarchy
        if interaction.user.id != interaction.guild.owner_id:  # Owner can kick anyone
            if user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> You cannot kick someone with an equal or higher role!",
                    ephemeral=True
                )
                return
        
        # Check if bot can kick this user (role hierarchy)
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot kick someone with an equal or higher role than me!",
                ephemeral=True
            )
            return
        
        try:
            # Try to DM the user before kicking
            try:
                dm_embed = discord.Embed(
                    title="<:kick:1426111903037390979> You have been kicked",
                    description=f"You have been kicked from **{interaction.guild.name}**",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                dm_embed.add_field(name="Note", value="You can rejoin using an invite link.", inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Kick the user
            await interaction.guild.kick(
                user, 
                reason=f"Kicked by {interaction.user} ({interaction.user.id}) - {reason}"
            )
            
            # Send success message
            embed = discord.Embed(
                title="<:kick:1426111903037390979> User Kicked",
                description=f"**{user}** (`{user.id}`) has been kicked from the server.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the kick (if you have a logging channel)
            # You can add logging functionality here
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to kick this user!",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Failed to kick user: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @kick.error
    async def kick_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You need 'Kick Members' permission to use this command!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {error}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(KickCog(bot))
