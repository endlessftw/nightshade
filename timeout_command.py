import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone


class TimeoutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='timeout', description='Timeout (mute) a user for a specified duration')
    @app_commands.describe(
        user='The user to timeout',
        duration='Duration (e.g., "30m" for 30 minutes, "2h" for 2 hours, "1d" for 1 day)',
        reason='Reason for the timeout (optional)'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        duration: str,
        reason: str = "No reason provided"
    ):
        # Check if bot has permission
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to timeout members!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to timeout themselves
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot timeout yourself!",
                ephemeral=True
            )
            return
        
        # Check if user is trying to timeout the bot
        if user.id == self.bot.user.id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot timeout myself!",
                ephemeral=True
            )
            return
        
        # Check if target user is the server owner
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You cannot timeout the server owner!",
                ephemeral=True
            )
            return
        
        # Check role hierarchy
        if interaction.user.id != interaction.guild.owner_id:  # Owner can timeout anyone
            if user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> You cannot timeout someone with an equal or higher role!",
                    ephemeral=True
                )
                return
        
        # Check if bot can timeout this user (role hierarchy)
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot timeout someone with an equal or higher role than me!",
                ephemeral=True
            )
            return
        
        # Parse duration
        try:
            duration_seconds = self.parse_duration(duration)
            if duration_seconds is None:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> Invalid duration format! Use format like: `30m` (minutes), `2h` (hours), or `1d` (days)",
                    ephemeral=True
                )
                return
            
            # Discord timeout limit is 28 days
            if duration_seconds > 28 * 24 * 60 * 60:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> Timeout duration cannot exceed 28 days!",
                    ephemeral=True
                )
                return
            
            if duration_seconds < 60:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> Timeout duration must be at least 1 minute!",
                    ephemeral=True
                )
                return
                
        except Exception:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Invalid duration format! Use format like: `30m` (minutes), `2h` (hours), or `1d` (days)",
                ephemeral=True
            )
            return
        
        try:
            # Calculate timeout end time (timezone-aware)
            timeout_until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
            
            # Try to DM the user before timing out
            try:
                dm_embed = discord.Embed(
                    title="<:timeout:1426116778395828244> You have been timed out",
                    description=f"You have been timed out in **{interaction.guild.name}**",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Duration", value=self.format_duration(duration_seconds), inline=False)
                dm_embed.add_field(name="Expires", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Timeout the user
            await user.timeout(
                timeout_until,
                reason=f"Timed out by {interaction.user} ({interaction.user.id}) - {reason}"
            )
            
            # Send success message
            embed = discord.Embed(
                title="<:timeout:1426116778395828244> User Timed Out",
                description=f"**{user}** (`{user.id}`) has been timed out.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=self.format_duration(duration_seconds), inline=True)
            embed.add_field(name="Expires", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the timeout (if you have a logging channel)
            # You can add logging functionality here
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to timeout this user!",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Failed to timeout user: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    def parse_duration(self, duration_str: str):
        """Parse duration string (e.g., '30m', '2h', '1d') into seconds"""
        duration_str = duration_str.strip().lower()
        
        if len(duration_str) < 2:
            return None
        
        # Extract number and unit
        number_str = duration_str[:-1]
        unit = duration_str[-1]
        
        try:
            number = int(number_str)
        except ValueError:
            return None
        
        if number <= 0:
            return None
        
        # Convert to seconds based on unit
        if unit == 'm':  # minutes
            return number * 60
        elif unit == 'h':  # hours
            return number * 3600
        elif unit == 'd':  # days
            return number * 86400
        else:
            return None
    
    def format_duration(self, seconds: int):
        """Format seconds into a human-readable duration string"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        return ", ".join(parts) if parts else "Less than a minute"
    
    @timeout.error
    async def timeout_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(TimeoutCog(bot))
