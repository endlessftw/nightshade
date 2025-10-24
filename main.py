import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import logging
from database import db

# Enable verbose logging for discord voice debugging. Keep root level at INFO to avoid too much noise.
logging.basicConfig(level=logging.INFO)
logging.getLogger('discord').setLevel(logging.DEBUG)
logging.getLogger('discord.voice_state').setLevel(logging.DEBUG)

# Try to load opus from a local DLL if available so voice works on Windows without system-wide install.
try:
    import discord.opus as _opus
    if not _opus.is_loaded():
        proj = pathlib.Path(__file__).parent
        # Common names to try
        for dll_name in ("opus.dll", "libopus.dll", "libopus-0.dll"):
            candidate = proj / dll_name
            if candidate.exists():
                try:
                    _opus.load_opus(str(candidate))
                    print(f"Loaded opus from {candidate}")
                    break
                except Exception as e:
                    print(f"Found {candidate} but failed to load opus from it: {e}")
        if not _opus.is_loaded():
            print("Opus not loaded. If you need voice support, place an appropriate 'opus.dll' in the bot folder or install libopus and ensure it's on PATH.")
except Exception:
    # Keep startup robust; missing opus module is okay until voice is used
    pass

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Queue for users waiting for a call: list of (user_id, channel)
call_queue = []
# Active calls: {user_id: (partner_id, channel)}
active_calls = {}

from discord import app_commands

# Expose database on the bot so commands can access it
bot.db = db

# Helper functions for backward compatibility with existing code
async def increment_userphone_messages(user_id: int):
    await db.increment_stat(user_id, 'userphone_messages')

async def increment_userphone_started(user_id: int):
    await db.increment_stat(user_id, 'userphone_started')

async def increment_win_tictactoe(user_id: int):
    await db.increment_stat(user_id, 'wins_tictactoe')

async def increment_win_connectfour(user_id: int):
    await db.increment_stat(user_id, 'wins_connectfour')

async def increment_win_rps(user_id: int):
    await db.increment_stat(user_id, 'wins_rps')

async def increment_win_hangman(user_id: int):
    await db.increment_stat(user_id, 'wins_hangman')

# Legacy compatibility: Provide save_stats that does nothing (DB auto-saves)
async def save_stats():
    pass  # No-op: database saves immediately

bot.save_stats = save_stats
bot.increment_userphone_messages = increment_userphone_messages
bot.increment_userphone_started = increment_userphone_started
bot.increment_win_tictactoe = increment_win_tictactoe
bot.increment_win_connectfour = increment_win_connectfour
bot.increment_win_rps = increment_win_rps
bot.increment_win_hangman = increment_win_hangman


# Timezone selector data (25 popular countries)
TIMEZONE_MAP = {
    "United States": ("Washington, D.C.", "America/New_York"),
    "United Kingdom": ("London", "Europe/London"),
    "France": ("Paris", "Europe/Paris"),
    "Germany": ("Berlin", "Europe/Berlin"),
    "Italy": ("Rome", "Europe/Rome"),
    "Spain": ("Madrid", "Europe/Madrid"),
    "Netherlands": ("Amsterdam", "Europe/Amsterdam"),
    "Sweden": ("Stockholm", "Europe/Stockholm"),
    "Russia": ("Moscow", "Europe/Moscow"),
    "Turkey": ("Ankara", "Europe/Istanbul"),
    "Japan": ("Tokyo", "Asia/Tokyo"),
    "China": ("Beijing", "Asia/Shanghai"),
    "India": ("New Delhi", "Asia/Kolkata"),
    "Australia": ("Canberra", "Australia/Sydney"),
    "Canada": ("Ottawa", "America/Toronto"),
    "Brazil": ("Brasilia", "America/Sao_Paulo"),
    "Mexico": ("Mexico City", "America/Mexico_City"),
    "Argentina": ("Buenos Aires", "America/Argentina/Buenos_Aires"),
    "Chile": ("Santiago", "America/Santiago"),
    "New Zealand": ("Wellington", "Pacific/Auckland"),
    "South Korea": ("Seoul", "Asia/Seoul"),
    "Singapore": ("Singapore", "Asia/Singapore"),
    "South Africa": ("Pretoria", "Africa/Johannesburg"),
    "Egypt": ("Cairo", "Africa/Cairo"),
    "UAE": ("Abu Dhabi", "Asia/Dubai"),
}

# Country flag emojis for embeds
COUNTRY_FLAG = {
    "United States": "🇺🇸",
    "United Kingdom": "🇬🇧",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Netherlands": "🇳🇱",
    "Sweden": "🇸🇪",
    "Russia": "🇷🇺",
    "Turkey": "🇹🇷",
    "Japan": "🇯🇵",
    "China": "🇨🇳",
    "India": "🇮🇳",
    "Australia": "🇦🇺",
    "Canada": "🇨🇦",
    "Brazil": "🇧🇷",
    "Mexico": "🇲🇽",
    "Argentina": "🇦🇷",
    "Chile": "🇨🇱",
    "New Zealand": "🇳🇿",
    "South Korea": "🇰🇷",
    "Singapore": "🇸🇬",
    "South Africa": "🇿🇦",
    "Egypt": "🇪🇬",
    "UAE": "🇦🇪",
}


@bot.tree.command(name="timezone", description="Show the current time in a capital city (choose a country).")
@app_commands.choices(country=[app_commands.Choice(name=country, value=country) for country in TIMEZONE_MAP.keys()])
async def timezone(interaction: discord.Interaction, country: app_commands.Choice[str]):
    country_name = country.value
    capital, tzname = TIMEZONE_MAP[country_name]
    # Try ZoneInfo first, fall back to pytz if ZoneInfo tzdata is missing on the system
    try:
        tz = ZoneInfo(tzname)
        now = datetime.now(tz)
    except Exception:
        # If ZoneInfo fails (system tzdata missing), try importing pytz dynamically.
        try:
            import importlib
            pytz = importlib.import_module('pytz')
            tz = pytz.timezone(tzname)
            now = datetime.now(tz)
        except ModuleNotFoundError:
            await interaction.response.send_message(
                "Timezone data is unavailable on this system. Install the 'tzdata' package (for ZoneInfo) or 'pytz' in your Python environment.",
                ephemeral=True,
            )
            return
        except Exception as e:
            await interaction.response.send_message(f"Failed to determine timezone: {e}", ephemeral=True)
            return

    offset = now.utcoffset() or __import__('datetime').timedelta(0)
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    hh = abs(total_seconds) // 3600
    mm = (abs(total_seconds) % 3600) // 60
    offset_str = f"UTC{sign}{hh:02d}:{mm:02d}"
    time_str = now.strftime("%A, %d %B %Y • %H:%M:%S")

    flag = COUNTRY_FLAG.get(country_name, "")
    embed = discord.Embed(title=f"<a:clock:1424650341651189772> Local time — {capital}, {country_name} {flag}", color=discord.Color.blurple())
    embed.add_field(name="Local Time", value=f"{time_str}", inline=False)
    embed.add_field(name="Timezone", value=f"{tzname} ({offset_str})", inline=False)
    embed.set_footer(text="Times shown in the capital city")

    await interaction.response.send_message(embed=embed, ephemeral=False)

from discord import app_commands

@bot.tree.command(name="userphone", description="Connects you to a random user from any server using the bot.")
async def userphone(interaction: discord.Interaction):
    user_id = interaction.user.id
    channel = interaction.channel
    if user_id in active_calls:
        await interaction.response.send_message("You are already in a call. Use /hangup to disconnect.", ephemeral=True)
        return
    if any(user_id == uid for uid, _ in call_queue):
        await interaction.response.send_message("You are already waiting for a call.", ephemeral=True)
        return
    # record that this user started a userphone
    try:
        await bot.increment_userphone_started(user_id)
    except Exception as e:
        print(f"Failed to save userphone start stat: {e}")
    call_queue.append((user_id, channel))
    # Track who initiated the call for each channel
    if not hasattr(bot, 'initiators'):
        bot.initiators = {}
    bot.initiators[channel.id] = user_id
    await interaction.response.send_message("<a:phone:1424654842491834449> **Waiting for another user...**", ephemeral=False)
    # Try to pair
    if len(call_queue) >= 2:
        (user1, channel1) = call_queue.pop(0)
        (user2, channel2) = call_queue.pop(0)
        active_calls[user1] = (user2, channel1)
        active_calls[user2] = (user1, channel2)
        # Notify both users in their channels
        for uid, ch in [(user1, channel1), (user2, channel2)]:
            try:
                await ch.send(f"<@{uid}> You are now connected! Type messages here to chat. Use /hangup to disconnect.")
            except Exception:
                pass

@bot.tree.command(name="hangup", description="Disconnects you from the current call or queue.")
async def hangup(interaction: discord.Interaction):
    user_id = interaction.user.id
    display_name = interaction.user.display_name
    channel = interaction.channel
    # Only allow the initiator to hang up the call (handle active calls first)
    initiator_id = getattr(bot, 'initiators', {}).get(channel.id)
    if user_id in active_calls:
        if initiator_id is not None and user_id != initiator_id:
            await interaction.response.send_message("You can't hang up the call because you weren't the one that started it.", ephemeral=True)
            return
        partner_id, user_channel = active_calls.pop(user_id)
        partner_info = active_calls.pop(partner_id, None)
        # Remove initiator tracking
        if hasattr(bot, 'initiators') and channel.id in bot.initiators:
            del bot.initiators[channel.id]
        # Notify both users in their channels
        try:
            await user_channel.send(f"**{display_name}** Call ended.")
        except Exception:
            pass
        if partner_info:
            partner_channel = partner_info[1]
            partner_name = None
            if hasattr(partner_channel, 'guild'):
                partner_member = partner_channel.guild.get_member(partner_id)
                if partner_member:
                    partner_name = partner_member.display_name
            if not partner_name:
                partner_name = f"User {partner_id}"
            try:
                await partner_channel.send(f"**{partner_name}** Call ended.")
            except Exception:
                pass
        await interaction.response.send_message("Call ended.", ephemeral=True)
        return

    # If not in an active call, remove from queue if waiting
    removed_from_queue = False
    for i, (uid, ch) in enumerate(call_queue):
        if uid == user_id:
            call_queue.pop(i)
            removed_from_queue = True
            try:
                await ch.send(f"**{display_name}** You have left the queue.")
            except Exception:
                pass
            break
    if removed_from_queue:
        # acknowledge the interaction without sending an extra ephemeral message
        await interaction.response.defer(ephemeral=True)
    else:
        await interaction.response.send_message("You are not in a call or queue.", ephemeral=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    # Connect to database
    try:
        await db.connect()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("Bot will continue but data will not persist!")
    
    # Set an initial presence showing how many servers the bot is in
    try:
        async def _update_presence():
            guild_count = len(bot.guilds)
            # Use a Watching activity so it appears like "Watching X servers"
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"{guild_count} servers ・ /help")
            await bot.change_presence(activity=activity)
        await _update_presence()
    except Exception as e:
        print(f"Failed to set presence: {e}")
    # Debug: list commands currently registered on the CommandTree
    # Load optional extensions before syncing so their commands are registered
    try:
        await bot.load_extension('ping_command')
        print('Loaded extension: ping_command')
    except Exception as e:
        print(f'Could not load ping_command extension: {e}')
    try:
        await bot.load_extension('timechannel_command')
        print('Loaded extension: timechannel_command')
    except Exception as e:
        print(f'Could not load timechannel_command extension: {e}')
    try:
        await bot.load_extension('help_command')
        print('Loaded extension: help_command')
    except Exception as e:
        print(f'Could not load help_command extension: {e}')
    try:
        await bot.load_extension('eightball_command')
        print('Loaded extension: eightball_command')
    except Exception as e:
        print(f'Could not load eightball_command extension: {e}')
    try:
        await bot.load_extension('ai_command')
        print('Loaded extension: ai_command')
    except Exception as e:
        print(f'Could not load ai_command extension: {e}')
    try:
        await bot.load_extension('quote_command')
        print('Loaded extension: quote_command')
    except Exception as e:
        print(f'Could not load quote_command extension: {e}')
    try:
        await bot.load_extension('coin_command')
        print('Loaded extension: coin_command')
    except Exception as e:
        print(f'Could not load coin_command extension: {e}')
    try:
        await bot.load_extension('aura_command')
        print('Loaded extension: aura_command')
    except Exception as e:
        print(f'Could not load aura_command extension: {e}')
    try:
        await bot.load_extension('shadow_command')
        print('Loaded extension: shadow_command')
    except Exception as e:
        print(f'Could not load shadow_command extension: {e}')
    try:
        await bot.load_extension('tictactoe_command')
        print('Loaded extension: tictactoe_command')
    except Exception as e:
        print(f'Could not load tictactoe_command extension: {e}')
    try:
        await bot.load_extension('connectfour_command')
        print('Loaded extension: connectfour_command')
    except Exception as e:
        print(f'Could not load connectfour_command extension: {e}')
    try:
        await bot.load_extension('myprofile_command')
        print('Loaded extension: myprofile_command')
    except Exception as e:
        print(f'Could not load myprofile_command extension: {e}')
    try:
        await bot.load_extension('snipe_command')
        print('Loaded extension: snipe_command')
    except Exception as e:
        print(f'Could not load snipe_command extension: {e}')
    try:
        await bot.load_extension('rockpaperscissor_command')
        print('Loaded extension: rockpaperscissor_command')
    except Exception as e:
        print(f'Could not load rockpaperscissor_command extension: {e}')
    try:
        await bot.load_extension('play_command')
        print('Loaded extension: play_command')
    except Exception as e:
        print(f'Could not load play_command extension: {e}')
    try:
        await bot.load_extension('askreddit_command')
        print('Loaded extension: askreddit_command')
    except Exception as e:
        print(f'Could not load askreddit_command extension: {e}')
    try:
        await bot.load_extension('hangman_command')
        print('Loaded extension: hangman_command')
    except Exception as e:
        print(f'Could not load hangman_command extension: {e}')
    try:
        await bot.load_extension('welcomer_command')
        print('Loaded extension: welcomer_command')
    except Exception as e:
        print(f'Could not load welcomer_command extension: {e}')
    try:
        await bot.load_extension('giveaway_command')
        print('Loaded extension: giveaway_command')
    except Exception as e:
        print(f'Could not load giveaway_command extension: {e}')
    try:
        await bot.load_extension('ban_command')
        print('Loaded extension: ban_command')
    except Exception as e:
        print(f'Could not load ban_command extension: {e}')
    try:
        await bot.load_extension('kick_command')
        print('Loaded extension: kick_command')
    except Exception as e:
        print(f'Could not load kick_command extension: {e}')
    try:
        await bot.load_extension('userprofile_command')
        print('Loaded extension: userprofile_command')
    except Exception as e:
        print(f'Could not load userprofile_command extension: {e}')
    try:
        await bot.load_extension('timeout_command')
        print('Loaded extension: timeout_command')
    except Exception as e:
        print(f'Could not load timeout_command extension: {e}')
    try:
        await bot.load_extension('untimeout_command')
        print('Loaded extension: untimeout_command')
    except Exception as e:
        print(f'Could not load untimeout_command extension: {e}')
    try:
        await bot.load_extension('ship_command')
        print('Loaded extension: ship_command')
    except Exception as e:
        print(f'Could not load ship_command extension: {e}')
    try:
        await bot.load_extension('warn_command')
        print('Loaded extension: warn_command')
    except Exception as e:
        print(f'Could not load warn_command extension: {e}')
    try:
        await bot.load_extension('unwarn_command')
        print('Loaded extension: unwarn_command')
    except Exception as e:
        print(f'Could not load unwarn_command extension: {e}')
    try:
        await bot.load_extension('purge_command')
        print('Loaded extension: purge_command')
    except Exception as e:
        print(f'Could not load purge_command extension: {e}')
    try:
        await bot.load_extension('lock_command')
        print('Loaded extension: lock_command')
    except Exception as e:
        print(f'Could not load lock_command extension: {e}')
    try:
        await bot.load_extension('unlock_command')
        print('Loaded extension: unlock_command')
    except Exception as e:
        print(f'Could not load unlock_command extension: {e}')
    try:
        await bot.load_extension('truthordare_command')
        print('Loaded extension: truthordare_command')
    except Exception as e:
        print(f'Could not load truthordare_command extension: {e}')
    # logo_command removed

    try:
        cmds = [c.name for c in bot.tree.walk_commands()]
        print(f"Commands in tree before sync: {cmds}")
        print(f"Total commands found: {len(cmds)}")
    except Exception as e:
        print(f"Error listing commands: {e}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Update presence when the bot joins a guild
    try:
        guild_count = len(bot.guilds)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{guild_count} servers")
        await bot.change_presence(activity=activity)
        print(f"Joined guild {guild.name} ({guild.id}), updated presence to {guild_count} servers")
    except Exception as e:
        print(f"Failed to update presence on guild join: {e}")


@bot.event
async def on_guild_remove(guild: discord.Guild):
    # Update presence when the bot is removed from a guild
    try:
        guild_count = len(bot.guilds)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{guild_count} servers")
        await bot.change_presence(activity=activity)
        print(f"Removed from guild {guild.name} ({guild.id}), updated presence to {guild_count} servers")
    except Exception as e:
        print(f"Failed to update presence on guild remove: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = message.author.id
    # Relay any non-bot message sent in a userphone channel
    if not message.author.bot:
        # Check if this channel is an active userphone channel
        for uid, (partner_id, user_channel) in active_calls.items():
            if message.channel == user_channel:
                partner_info = active_calls.get(partner_id)
                if partner_info:
                    partner_channel = partner_info[1]
                    try:
                        sender_name = message.author.display_name
                        # increment message count for sender
                        try:
                            await bot.increment_userphone_messages(message.author.id)
                        except Exception as e:
                            print(f"Failed to save userphone message stat: {e}")
                        await partner_channel.send(f"**{sender_name}**📞: {message.content}")
                    except Exception:
                        await message.channel.send("Failed to deliver message.")
                break
    await bot.process_commands(message)

# To run the bot, add your token below
import os
# Optional: load a .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TOKEN = os.environ.get('DISCORD_TOKEN') or os.environ.get('TOKEN')
if not TOKEN:
    print("ERROR: Discord bot token not found!")
    print("Please set the DISCORD_TOKEN or TOKEN environment variable.")
    raise RuntimeError("Discord bot token not found. Please set the DISCORD_TOKEN environment variable.")

if __name__ == '__main__':
    # Helpful reminder for operators
    print('Starting bot — ensure DISCORD_TOKEN is set in your environment.')
    print('Attempting to connect to Discord...')
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"FATAL ERROR: Bot failed to start: {e}")
        import traceback
        traceback.print_exc()
        raise
