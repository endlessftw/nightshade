import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import typing
from collections import deque

# Store the last 10 deleted messages per channel on the bot instance when the cog is loaded.
# Data shape: {channel_id: deque([{'author': discord.User, 'content': str, 'attachments': [discord.Attachment], 'created_at': datetime}], maxlen=10)}

class SnipeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Keep a small in-memory cache on the bot to be shared between cogs if desired
        if not hasattr(bot, 'deleted_messages'):
            bot.deleted_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return
        try:
            # Initialize deque for this channel if it doesn't exist
            if message.channel.id not in self.bot.deleted_messages:
                self.bot.deleted_messages[message.channel.id] = deque(maxlen=10)
            
            # Add the deleted message to the front of the deque
            self.bot.deleted_messages[message.channel.id].appendleft({
                'author': message.author,
                'content': message.content,
                'attachments': list(message.attachments),
                'created_at': message.created_at or datetime.utcnow(),
            })
        except Exception:
            # Don't let caching failures crash the bot
            pass

    @app_commands.command(name="snipe", description="Show the last 10 deleted messages in this channel.")
    async def snipe(self, interaction: discord.Interaction):
        chan = interaction.channel
        if chan is None:
            await interaction.response.send_message("<a:warning:1424944783587147868> Could not determine the channel.", ephemeral=True)
            return

        records = getattr(self.bot, 'deleted_messages', {}).get(chan.id)
        if not records or len(records) == 0:
            await interaction.response.send_message("<a:warning:1424944783587147868> No recently deleted messages found in this channel.", ephemeral=True)
            return

        # Create an embed showing all deleted messages
        embed = discord.Embed(
            title=f"<:snipe:1425275228900036753> Last {len(records)} deleted message(s) in #{chan.name}",
            color=discord.Color.dark_green(),
            timestamp=datetime.utcnow(),
        )
        
        # Add each deleted message as a field
        for idx, record in enumerate(records, 1):
            author = record.get('author')
            content = record.get('content') or "(no text content)"
            attachments = record.get('attachments') or []
            created_at = record.get('created_at')
            
            # Get author name
            display_name = getattr(author, 'display_name', None) or getattr(author, 'name', None) or str(author)
            
            # Format timestamp
            time_str = f"<t:{int(created_at.timestamp())}:R>" if created_at else "Unknown time"
            
            # Truncate content if too long
            if len(content) > 200:
                content = content[:200] + "..."
            
            # Add attachment info
            attachment_info = ""
            if attachments:
                attachment_info = f"\n📎 {len(attachments)} attachment(s)"
            
            # Add field for this message
            field_value = f"{content}{attachment_info}\n{time_str}"
            embed.add_field(
                name=f"#{idx} - {display_name}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SnipeCog(bot))
