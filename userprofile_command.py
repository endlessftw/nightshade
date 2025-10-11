import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime


class UserProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='userprofile', description='View detailed information about a user')
    @app_commands.describe(
        user='The user to view (leave empty to view yourself)'
    )
    async def userprofile(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member = None
    ):
        # Defer the response to prevent timeout
        await interaction.response.defer()
        
        # If no user specified, show the command author's profile
        if user is None:
            user = interaction.user
        
        # Get user status
        status_emoji = {
            discord.Status.online: "<:online:1424944783587147868>",
            discord.Status.idle: "<:idle:1424944783587147868>",
            discord.Status.dnd: "<:dnd:1424944783587147868>",
            discord.Status.offline: "<:offline:1424944783587147868>"
        }
        status = status_emoji.get(user.status, "❓")
        
        # Create embed
        embed = discord.Embed(
            title=f"{user.name}'s Profile",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Set thumbnail to user's avatar
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Basic Information
        embed.add_field(
            name="<:profile:1426112264964018187> Basic Info",
            value=f"**Username:** {user.name}\n"
                  f"**Display Name:** {user.display_name}\n"
                  f"**ID:** `{user.id}`\n"
                  f"**Status:** {status} {user.status}\n"
                  f"**Bot:** {'Yes' if user.bot else 'No'}",
            inline=False
        )
        
        # Account Creation
        created_at = user.created_at
        created_timestamp = int(created_at.timestamp())
        embed.add_field(
            name="📅 Account Created",
            value=f"<t:{created_timestamp}:F>\n(<t:{created_timestamp}:R>)",
            inline=True
        )
        
        # Server Join Date
        if user.joined_at:
            joined_at = user.joined_at
            joined_timestamp = int(joined_at.timestamp())
            embed.add_field(
                name="📥 Joined Server",
                value=f"<t:{joined_timestamp}:F>\n(<t:{joined_timestamp}:R>)",
                inline=True
            )
        
        # Roles
        if len(user.roles) > 1:  # Exclude @everyone
            roles = [role.mention for role in reversed(user.roles) if role.name != "@everyone"]
            roles_text = ", ".join(roles[:10])  # Limit to 10 roles to avoid embed length issues
            if len(user.roles) > 11:
                roles_text += f" *and {len(user.roles) - 11} more...*"
            embed.add_field(
                name=f"🎭 Roles ({len(user.roles) - 1})",
                value=roles_text,
                inline=False
            )
        
        # Key Permissions
        key_perms = []
        if user.guild_permissions.administrator:
            key_perms.append("Administrator")
        if user.guild_permissions.manage_guild:
            key_perms.append("Manage Server")
        if user.guild_permissions.manage_roles:
            key_perms.append("Manage Roles")
        if user.guild_permissions.manage_channels:
            key_perms.append("Manage Channels")
        if user.guild_permissions.kick_members:
            key_perms.append("Kick Members")
        if user.guild_permissions.ban_members:
            key_perms.append("Ban Members")
        if user.guild_permissions.manage_messages:
            key_perms.append("Manage Messages")
        
        if key_perms:
            embed.add_field(
                name="🔑 Key Permissions",
                value=", ".join(key_perms),
                inline=False
            )
        
        # Server Boost Status
        if user.premium_since:
            boost_timestamp = int(user.premium_since.timestamp())
            embed.add_field(
                name="💎 Server Booster",
                value=f"Boosting since <t:{boost_timestamp}:R>",
                inline=False
            )
        
        # Activity
        if user.activities:
            activity = user.activities[0]
            activity_text = ""
            
            if isinstance(activity, discord.Game):
                activity_text = f"🎮 Playing **{activity.name}**"
            elif isinstance(activity, discord.Streaming):
                activity_text = f"📡 Streaming **{activity.name}**"
            elif isinstance(activity, discord.Spotify):
                activity_text = f"🎵 Listening to **{activity.title}** by {activity.artist}"
            elif isinstance(activity, discord.CustomActivity):
                activity_text = f"💭 {activity.name or 'Custom Status'}"
            elif isinstance(activity, discord.Activity):
                activity_text = f"**{activity.name}**"
            
            if activity_text:
                embed.add_field(
                    name="🎯 Current Activity",
                    value=activity_text,
                    inline=False
                )
        
        # Set footer
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UserProfileCog(bot))
