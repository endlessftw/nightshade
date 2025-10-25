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
        
        # Defer the response immediately
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            # Interaction already expired
            return
        
        # Get the @everyone role
        everyone_role = interaction.guild.default_role
        
        # Get current channel permissions for @everyone
        overwrites = interaction.channel.overwrites_for(everyone_role)
        
        # Check if channel is already locked
        if overwrites.send_messages == False:
            try:
                await interaction.followup.send(
                    "<:lock:1431413547010621511> This channel is already locked.",
                    ephemeral=True
                )
            except:
                pass
            return
        
        # Lock the channel by denying send_messages permission
        try:
            overwrites.send_messages = False
            await interaction.channel.set_permissions(everyone_role, overwrite=overwrites)
        except discord.Forbidden as e:
            # Only show permission error if the lock itself failed
            print(f"[lock] Permission error during locking: {e}")
            try:
                await interaction.followup.send(
                    "<a:warning:1424944783587147868> I don't have permission to this channel.",
                    ephemeral=True
                )
            except:
                pass
            return
        except Exception as e:
            print(f"[lock] Error during locking: {e}")
            try:
                await interaction.followup.send(
                    f"<a:warning:1424944783587147868> An error occurred: {str(e)}",
                    ephemeral=True
                )
            except:
                pass
            return
        
        # Send confirmation embed AFTER locking (wrapped in try-except)
        try:
            embed = discord.Embed(
                title="<:lock:1431413547010621511> Channel Locked",
                description=f"This channel has been locked by {interaction.user.mention}.\nOnly moderators can send messages.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed)
        except discord.Forbidden:
            print("[lock] Bot doesn't have permission to send messages in this channel")
        except Exception as e:
            print(f"[lock] Error sending embed: {e}")
        
        # Delete the interaction response (no private message)
        try:
            await interaction.delete_original_response()
        except discord.Forbidden:
            # Ignore permission errors when deleting
            pass
        except discord.NotFound:
            # Response was already deleted or doesn't exist
            pass
        except Exception as e:
            # Ignore other errors when deleting
            print(f"[lock] Error deleting response: {e}")
    
    @lock.error
    async def lock_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the lock command"""
        if isinstance(error, app_commands.errors.MissingPermissions):
            try:
                # Check if interaction was already responded to
                if interaction.response.is_done():
                    await interaction.followup.send(
                        "<a:warning:1424944783587147868> You don't have permission to use this command. You need the `Manage Channels` permission.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "<a:warning:1424944783587147868> You don't have permission to use this command. You need the `Manage Channels` permission.",
                        ephemeral=True
                    )
            except:
                # Silently fail if we can't send the error message
                pass
        else:
            # Log the error but don't try to send a message
            print(f"[lock_error] Error occurred: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(LockCog(bot))
