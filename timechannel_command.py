import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import pytz
import json
import os

# Map of city names to their timezones (using pytz timezone names)
CITY_TIMEZONES = {
    'New York': 'America/New_York',
    'Los Angeles': 'America/Los_Angeles',
    'Chicago': 'America/Chicago',
    'London': 'Europe/London',
    'Paris': 'Europe/Paris',
    'Tokyo': 'Asia/Tokyo',
    'Sydney': 'Australia/Sydney',
    'Dubai': 'Asia/Dubai',
    'Hong Kong': 'Asia/Hong_Kong',
    'Singapore': 'Asia/Singapore',
    'Moscow': 'Europe/Moscow',
    'Berlin': 'Europe/Berlin',
    'Toronto': 'America/Toronto',
    'Mumbai': 'Asia/Kolkata',
    'Beijing': 'Asia/Shanghai',
    'Seoul': 'Asia/Seoul',
    'Mexico City': 'America/Mexico_City',
    'Sao Paulo': 'America/Sao_Paulo',
    'Istanbul': 'Europe/Istanbul',
    'Cairo': 'Africa/Cairo',
    'Lagos': 'Africa/Lagos',
    'Johannesburg': 'Africa/Johannesburg',
    'Bangkok': 'Asia/Bangkok',
    'Jakarta': 'Asia/Jakarta',
    'Manila': 'Asia/Manila',
}

# Map of city names to their country flags
CITY_FLAGS = {
    'New York': '🇺🇸',
    'Los Angeles': '🇺🇸',
    'Chicago': '🇺🇸',
    'London': '🇬🇧',
    'Paris': '🇫🇷',
    'Tokyo': '🇯🇵',
    'Sydney': '🇦🇺',
    'Dubai': '🇦🇪',
    'Hong Kong': '🇭🇰',
    'Singapore': '🇸🇬',
    'Moscow': '🇷🇺',
    'Berlin': '🇩🇪',
    'Toronto': '🇨🇦',
    'Mumbai': '🇮🇳',
    'Beijing': '🇨🇳',
    'Seoul': '🇰🇷',
    'Mexico City': '🇲🇽',
    'Sao Paulo': '🇧🇷',
    'Istanbul': '🇹🇷',
    'Cairo': '🇪🇬',
    'Lagos': '🇳🇬',
    'Johannesburg': '🇿🇦',
    'Bangkok': '🇹🇭',
    'Jakarta': '🇮🇩',
    'Manila': '🇵🇭',
}

# Emoji clock faces for different hours
CLOCK_EMOJIS = {
    0: '', 1: '', 2: '', 3: '', 4: '', 5: '',
    6: '', 7: '', 8: '', 9: '', 10: '', 11: '',
    12: '', 13: '', 14: '', 15: '', 16: '', 17: '',
    18: '', 19: '', 20: '', 21: '', 22: '', 23: '',
}


class TimeChannelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dictionary to store {message_id: {'channel_id': int, 'guild_id': int, 'cities': [str]}}
        self.time_messages = {}
        self.config_file = os.path.join(os.path.dirname(__file__), 'timechannel_config.json')
        # Load saved time messages
        self.load_config()
        # Start the update loop
        self.update_time_messages.start()
    
    def cog_unload(self):
        """Stop the update loop when the cog is unloaded"""
        self.update_time_messages.cancel()
    
    @app_commands.command(name='timechannel', description='Create an auto-updating time display for selected cities')
    @app_commands.describe(
        city1='First city to display',
        city2='Second city to display (optional)',
        city3='Third city to display (optional)',
        city4='Fourth city to display (optional)',
        city5='Fifth city to display (optional)'
    )
    @app_commands.choices(
        city1=[app_commands.Choice(name=city, value=city) for city in sorted(CITY_TIMEZONES.keys())],
        city2=[app_commands.Choice(name=city, value=city) for city in sorted(CITY_TIMEZONES.keys())],
        city3=[app_commands.Choice(name=city, value=city) for city in sorted(CITY_TIMEZONES.keys())],
        city4=[app_commands.Choice(name=city, value=city) for city in sorted(CITY_TIMEZONES.keys())],
        city5=[app_commands.Choice(name=city, value=city) for city in sorted(CITY_TIMEZONES.keys())]
    )
    async def timechannel(
        self, 
        interaction: discord.Interaction, 
        city1: str,
        city2: str = None,
        city3: str = None,
        city4: str = None,
        city5: str = None
    ):
        # Collect selected cities
        cities = [city1]
        if city2:
            cities.append(city2)
        if city3:
            cities.append(city3)
        if city4:
            cities.append(city4)
        if city5:
            cities.append(city5)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_cities = []
        for city in cities:
            if city not in seen:
                seen.add(city)
                unique_cities.append(city)
        
        # Defer response as message creation might take time
        await interaction.response.defer()
        
        try:
            # Create the initial embed
            embed = self.create_time_embed(unique_cities)
            
            # Send the embed message
            message = await interaction.followup.send(embed=embed)
            
            # Store the message info
            self.time_messages[message.id] = {
                'channel_id': interaction.channel.id,
                'guild_id': interaction.guild.id,
                'cities': unique_cities
            }
            
            # Save to file
            self.save_config()
            
            print(f"[timechannel] Created time display for {len(unique_cities)} cities in guild {interaction.guild.name}")
            
        except Exception as e:
            await interaction.followup.send(
                f"<a:warning:1424944783587147868> Failed to create time display: {e}",
                ephemeral=True
            )
    
    def create_time_embed(self, cities):
        """Create an embed with current times for the specified cities"""
        embed = discord.Embed(
            title="<a:clock:1424655674142363668> World Time Display",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for city in cities:
            timezone_str = CITY_TIMEZONES.get(city)
            flag = CITY_FLAGS.get(city, '🌍')
            if timezone_str:
                try:
                    tz = pytz.timezone(timezone_str)
                    now = datetime.now(tz)
                    hour = now.hour
                    time_str = now.strftime('%I:%M:%S %p')
                    date_str = now.strftime('%A, %B %d, %Y')
                    clock_emoji = CLOCK_EMOJIS.get(hour, '🕐')
                    
                    embed.add_field(
                        name=f"{flag} {city}",
                        value=f"{clock_emoji} **{time_str}**\n{date_str}",
                        inline=False
                    )
                except Exception as e:
                    print(f"[timechannel] Error getting time for {city}: {e}")
        
        embed.set_footer(text="Updates every minute  Times are local to each city")
        return embed
    
    @tasks.loop(seconds=60)
    async def update_time_messages(self):
        """Update all time display messages every minute at the start of each minute"""
        messages_to_remove = []
        
        for message_id, info in list(self.time_messages.items()):
            try:
                # Validate that info has the required keys (skip old voice channel entries)
                if not isinstance(info, dict) or 'channel_id' not in info or 'cities' not in info:
                    messages_to_remove.append(message_id)
                    continue
                
                # Get the channel
                channel = self.bot.get_channel(info['channel_id'])
                if not channel:
                    messages_to_remove.append(message_id)
                    continue
                
                # Try to fetch the message
                try:
                    message = await channel.fetch_message(message_id)
                except discord.errors.NotFound:
                    # Message was deleted
                    messages_to_remove.append(message_id)
                    continue
                
                # Create updated embed
                embed = self.create_time_embed(info['cities'])
                
                # Edit the message
                await message.edit(embed=embed)
                
            except discord.errors.Forbidden:
                print(f"[timechannel] Missing permissions for message {message_id}")
            except Exception as e:
                print(f"[timechannel] Error updating message {message_id}: {e}")
                # If there's a persistent error, mark for removal
                messages_to_remove.append(message_id)
        
        # Remove messages that no longer exist
        if messages_to_remove:
            for message_id in messages_to_remove:
                del self.time_messages[message_id]
            self.save_config()
            print(f"[timechannel] Removed {len(messages_to_remove)} deleted message(s)")
    
    @update_time_messages.before_loop
    async def before_update_time_messages(self):
        """Wait until the bot is ready and sync to the start of the next minute"""
        import asyncio
        await self.bot.wait_until_ready()
        
        # Wait until the start of the next minute
        now = datetime.now()
        # Calculate seconds until next minute
        seconds_to_wait = 60 - now.second
        
        print(f"[timechannel] Waiting {seconds_to_wait} seconds to sync to the next minute...")
        await asyncio.sleep(seconds_to_wait)
        print(f"[timechannel] Synced! Updates will now occur at the start of each minute.")
    
    @update_time_messages.error
    async def update_time_messages_error(self, error):
        """Handle errors in the update loop and keep it running"""
        print(f"[timechannel] Error in update loop: {error}")
    
    def load_config(self):
        """Load time message configuration from file"""
        try:
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to integers and validate format
                    valid_messages = {}
                    for k, v in data.items():
                        # Only load entries with the new format (channel_id and cities)
                        if isinstance(v, dict) and 'channel_id' in v and 'cities' in v:
                            valid_messages[int(k)] = v
                    
                    self.time_messages = valid_messages
                    
                    if valid_messages:
                        print(f"[timechannel] Loaded {len(valid_messages)} time message(s)")
                    
                    # If we filtered out invalid entries, save the cleaned config
                    if len(valid_messages) != len(data):
                        print(f"[timechannel] Cleaned up {len(data) - len(valid_messages)} invalid entry(ies)")
                        self.save_config()
        except Exception as e:
            print(f"[timechannel] Error loading config: {e}")
            self.time_messages = {}
    
    def save_config(self):
        """Save time message configuration to file"""
        try:
            # Convert integer keys to strings for JSON
            data = {str(k): v for k, v in self.time_messages.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[timechannel] Saved configuration")
        except Exception as e:
            print(f"[timechannel] Error saving config: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(TimeChannelCog(bot))
