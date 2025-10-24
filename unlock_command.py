import discord
from discord.ext import commands
from discord import app_commands


class UnlockCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="unlock", description="Unlock the channel so everyone can send messages again.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        """Unlock a channel so everyone can type"""
        
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get the @everyone role
            everyone_role = interaction.guild.default_role
            
            # Get current channel permissions for @everyone
            overwrites = interaction.channel.overwrites_for(everyone_role)
            
            # Check if channel is already unlocked
            if overwrites.send_messages != False:
                await interaction.followup.send(
                    "<:unlock:1431411741950218342> This channel is already unlocked.",
                    ephemeral=True
                )
                return
            
            # Unlock the channel by resetting send_messages permission to None (inherit from category/server)
            overwrites.send_messages = None
            await interaction.channel.set_permissions(everyone_role, overwrite=overwrites)
            
            # Send confirmation in the channel
            embed = discord.Embed(
                title="<:unlock:1431411741950218342> Channel Unlocked",
                description=f"This channel has been unlocked by {interaction.user.mention}.\nEveryone can send messages again.",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed)
            
            # Send ephemeral confirmation to the moderator
            await interaction.followup.send(
                f"<:unlock:1431411741950218342> Successfully unlocked {interaction.channel.mention}.",
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
    
    @unlock.error
    async def unlock_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the unlock command"""
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
    await bot.add_cog(UnlockCog(bot))
