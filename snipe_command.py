import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import typing

# Store the last deleted message per channel on the bot instance when the cog is loaded.
# Data shape: {channel_id: {'author': discord.User, 'content': str, 'attachments': [discord.Attachment], 'created_at': datetime}}

class SnipeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Keep a small in-memory cache on the bot to be shared between cogs if desired
        if not hasattr(bot, 'last_deleted_message'):
            bot.last_deleted_message = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return
        try:
            self.bot.last_deleted_message[message.channel.id] = {
                'author': message.author,
                'content': message.content,
                'attachments': list(message.attachments),
                'created_at': message.created_at or datetime.utcnow(),
            }
        except Exception:
            # Don't let caching failures crash the bot
            pass

    @app_commands.command(name="snipe", description="Show the last deleted message in this channel.")
    async def snipe(self, interaction: discord.Interaction):
        chan = interaction.channel
        if chan is None:
            await interaction.response.send_message("<a:warning:1424944783587147868> Could not determine the channel.", ephemeral=True)
            return

        record = getattr(self.bot, 'last_deleted_message', {}).get(chan.id)
        if not record:
            await interaction.response.send_message("<a:warning:1424944783587147868> No recently deleted messages found in this channel.", ephemeral=True)
            return

        author = record.get('author')
        content = record.get('content') or "(no text content)"
        attachments = record.get('attachments') or []
        created_at = record.get('created_at')

        embed = discord.Embed(
            title=f"<:snipe:1425275228900036753> Last deleted message in #{chan.name}",
            description=content,
            color=discord.Color.dark_green(),
            timestamp=created_at,
        )
        # Prefer the user's display name (server-specific nick) and a robust avatar URL
        display_name = getattr(author, 'display_name', None) or getattr(author, 'name', None) or str(author)
        # Obtain an avatar URL in a version-compatible way
        avatar_url = None
        try:
            # discord.py v2: display_avatar is preferred
            avatar_url = author.display_avatar.url
        except Exception:
            try:
                # older attribute names
                avatar_url = author.avatar.url if getattr(author, 'avatar', None) else None
            except Exception:
                avatar_url = None

        embed.set_author(name=display_name, icon_url=avatar_url)
        embed.set_footer(text=f"Author ID: {getattr(author, 'id', 'unknown')}")

        # If attachments exist, and the first is an image, attach it to the embed display
        files = []
        try:
            if attachments:
                # If the first attachment is an image, set it as embed image
                first = attachments[0]
                if first.content_type and first.content_type.startswith('image'):
                    embed.set_image(url=first.url)
                else:
                    # For non-image attachments, list their filenames
                    names = '\n'.join(a.filename for a in attachments)
                    embed.add_field(name="Attachments", value=names, inline=False)
        except Exception:
            # If attachment properties aren't accessible, skip gracefully
            pass

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SnipeCog(bot))
