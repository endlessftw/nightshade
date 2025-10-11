import discord
from discord.ext import commands
from discord import app_commands


class UntimeoutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='untimeout', description='Remove timeout from a user')
    @app_commands.describe(
        user='The user to remove timeout from',
        reason='Reason for removing the timeout (optional)'
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member, 
        reason: str = "No reason provided"
    ):
        # Check if bot has permission
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to remove timeouts!",
                ephemeral=True
            )
            return
        
        # Check if user is actually timed out
        if user.timed_out_until is None:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> This user is not currently timed out!",
                ephemeral=True
            )
            return
        
        # Check role hierarchy
        if interaction.user.id != interaction.guild.owner_id:  # Owner can untimeout anyone
            if user.top_role >= interaction.user.top_role:
                await interaction.response.send_message(
                    "<a:warning:1424944783587147868> You cannot remove timeout from someone with an equal or higher role!",
                    ephemeral=True
                )
                return
        
        # Check if bot can untimeout this user (role hierarchy)
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I cannot remove timeout from someone with an equal or higher role than me!",
                ephemeral=True
            )
            return
        
        try:
            # Remove timeout by setting it to None
            await user.timeout(
                None,
                reason=f"Timeout removed by {interaction.user} ({interaction.user.id}) - {reason}"
            )
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="<:unmute:1426118353063248005> Your timeout has been removed",
                    description=f"Your timeout in **{interaction.guild.name}** has been removed.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled or blocked the bot
            
            # Send success message
            embed = discord.Embed(
                title="<:unmute:1426118353063248005> Timeout Removed",
                description=f"**{user}** (`{user.id}`) is no longer timed out.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the untimeout (if you have a logging channel)
            # You can add logging functionality here
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> I don't have permission to remove timeout from this user!",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> Failed to remove timeout: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {e}",
                ephemeral=True
            )
    
    @untimeout.error
    async def untimeout_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(UntimeoutCog(bot))
