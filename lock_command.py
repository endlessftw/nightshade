import discord
from discord.ext import commands
from discord import app_commands


class LockCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="lock", description="Lock the channel so only moderators can send messages.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        """Lock a channel so only moderators can type"""
        
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get the @everyone role
            everyone_role = interaction.guild.default_role
            
            # Get current channel permissions for @everyone
            overwrites = interaction.channel.overwrites_for(everyone_role)
            
            # Check if channel is already locked
            if overwrites.send_messages == False:
                await interaction.followup.send(
                    "<:lock:1431413547010621511> This channel is already locked.",
                    ephemeral=True
                )
                return
            
            # Lock the channel by denying send_messages permission
            overwrites.send_messages = False
            await interaction.channel.set_permissions(everyone_role, overwrite=overwrites)
            
            # Send confirmation in the channel
            embed = discord.Embed(
                title="<:lock:1431413547010621511> Channel Locked",
                description=f"This channel has been locked by {interaction.user.mention}.\nOnly moderators can send messages.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed)
            
            # Send ephemeral confirmation to the moderator
            await interaction.followup.send(
                f"<:lock:1431413547010621511> Successfully locked {interaction.channel.mention}.",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "<a:warning:1424944783587147868> I don't have permission to manage this channel.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"<a:warning:1424944783587147868> An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @lock.error
    async def lock_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the lock command"""
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You don't have permission to use this command. You need the `Manage Channels` permission.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"<a:warning:1424944783587147868> An error occurred: {str(error)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LockCog(bot))
