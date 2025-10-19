import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import json
import os
from datetime import datetime, timedelta


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = getattr(bot, 'db', None)
        self.active_giveaways = {}
        self.config_file = os.path.join(os.path.dirname(__file__), 'giveaway_config.json')
        self._config_loaded = False
        # Load config after bot is ready
        self.bot.loop.create_task(self._delayed_load_config())
    
    @app_commands.command(name='giveaway', description='Start a giveaway in the current channel')
    @app_commands.describe(
        duration='Duration (e.g., "30m" for 30 minutes, "2h" for 2 hours, "1d" for 1 day)',
        winners='Number of winners',
        prize='What are you giving away?'
    )
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        # Check if user has permission to manage messages
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> You need 'Manage Messages' permission to use this command.",
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
        except Exception:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Invalid duration format! Use format like: `30m` (minutes), `2h` (hours), or `1d` (days)",
                ephemeral=True
            )
            return
        
        # Validate winners count
        if winners < 1:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Number of winners must be at least 1!",
                ephemeral=True
            )
            return
        
        if winners > 20:
            await interaction.response.send_message(
                "<a:warning:1424944783587147868> Maximum 20 winners allowed!",
                ephemeral=True
            )
            return
        
        # Calculate end time (using timezone-aware datetime)
        from datetime import timezone
        end_time = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
        
        # Create giveaway embed
        embed = discord.Embed(
            title="<a:giveaway:1426084232249212969> GIVEAWAY <a:giveaway:1426084232249212969>",
            description=f"**Prize:** {prize}\n\n"
                       f"React with <a:giveaway:1426084232249212969> to enter!\n\n"
                       f"**Winners:** {winners}\n"
                       f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
                       f"**Hosted by:** {interaction.user.mention}",
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.set_footer(text=f"{winners} winner(s) • Use !reroll to reroll winners")
        
        # Send the giveaway message
        await interaction.response.defer()
        giveaway_message = await interaction.channel.send(embed=embed)
        
        # Add reaction
        await giveaway_message.add_reaction("<a:giveaway:1426084232249212969>")
        
        # Store giveaway info
        self.active_giveaways[giveaway_message.id] = {
            'channel_id': interaction.channel.id,
            'guild_id': interaction.guild.id,
            'host_id': interaction.user.id,
            'prize': prize,
            'winners_count': winners,
            'end_time': end_time.isoformat(),
            'ended': False
        }
        await self.save_config()
        
        # Acknowledge the interaction (required but silent)
        try:
            await interaction.followup.send("_ _", ephemeral=True, delete_after=0.1)
        except:
            pass
        
        # Schedule the giveaway to end
        await asyncio.sleep(duration_seconds)
        await self.end_giveaway(giveaway_message.id)
    
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
    
    async def end_giveaway(self, message_id: int):
        """End a giveaway and pick winners"""
        if message_id not in self.active_giveaways:
            print(f"[giveaway] end_giveaway called but {message_id} not in active giveaways")
            return
        
        giveaway_info = self.active_giveaways[message_id]
        
        if giveaway_info['ended']:
            print(f"[giveaway] Giveaway {message_id} already ended, skipping")
            return
        
        print(f"[giveaway] Ending giveaway {message_id}")
        
        try:
            # Get the channel and message
            channel = self.bot.get_channel(giveaway_info['channel_id'])
            if not channel:
                print(f"[giveaway] Channel {giveaway_info['channel_id']} not found for giveaway {message_id}")
                del self.active_giveaways[message_id]
                await self.save_config()
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.errors.NotFound:
                print(f"[giveaway] Message {message_id} not found in channel {channel.name}")
                del self.active_giveaways[message_id]
                await self.save_config()
                return
            except Exception as e:
                print(f"[giveaway] Error fetching message {message_id}: {e}")
                # Mark as ended even if we can't fetch the message
                giveaway_info['ended'] = True
                await self.save_config()
                return
            
            # Get users who reacted with the giveaway emoji
            reaction = None
            target_emoji_id = "1426084232249212969"  # The ID of the giveaway emoji
            print(f"[giveaway] Checking reactions on message {message_id}")
            print(f"[giveaway] Total reactions on message: {len(message.reactions)}")
            for r in message.reactions:
                print(f"[giveaway] Found reaction: {r.emoji} (type: {type(r.emoji).__name__}) - Count: {r.count}")
                # Check if it's a custom emoji and matches our ID
                emoji_str = str(r.emoji)
                if target_emoji_id in emoji_str:
                    reaction = r
                    print(f"[giveaway] ✓ Matched giveaway reaction with {r.count} reactions!")
                    break
            
            if not reaction:
                # No reactions
                embed = discord.Embed(
                    title="<a:giveaway:1426084232249212969> GIVEAWAY ENDED <a:giveaway:1426084232249212969>",
                    description=f"**Prize:** {giveaway_info['prize']}\n\n"
                               f"No valid entries! No winners could be determined.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Giveaway ended • Use !reroll to reroll winners")
                await message.edit(embed=embed)
                
                giveaway_info['ended'] = True
                await self.save_config()
                return
            
            # Get all users who reacted (excluding bots)
            # Need to fetch users with a limit to ensure we get all of them
            users = []
            print(f"[giveaway] Fetching users from reaction...")
            try:
                async for user in reaction.users(limit=None):
                    print(f"[giveaway] Found user: {user.name} (bot: {user.bot})")
                    if not user.bot:
                        users.append(user)
            except Exception as e:
                print(f"[giveaway] Error fetching reaction users: {e}")
                # Try alternative method
                users = [user for user in await reaction.users().flatten() if not user.bot]
            
            print(f"[giveaway] Total valid users (non-bots): {len(users)}")
            
            if len(users) == 0:
                # No valid entries
                embed = discord.Embed(
                    title="<a:giveaway:1426084232249212969> GIVEAWAY ENDED <a:giveaway:1426084232249212969>",
                    description=f"**Prize:** {giveaway_info['prize']}\n\n"
                               f"No valid entries! No winners could be determined.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Giveaway ended • Use !reroll to reroll winners")
                await message.edit(embed=embed)
                
                giveaway_info['ended'] = True
                await self.save_config()
                return
            
            # Pick winners
            winners_count = min(giveaway_info['winners_count'], len(users))
            winners = random.sample(users, winners_count)
            
            # Create winners list
            winners_mention = '\n'.join([f"<a:trophy:1424944527315042415> {winner.mention}" for winner in winners])
            
            # Update embed
            embed = discord.Embed(
                title="<a:giveaway:1426084232249212969> GIVEAWAY ENDED <a:giveaway:1426084232249212969>",
                description=f"**Prize:** {giveaway_info['prize']}\n\n"
                           f"**Winner(s):**\n{winners_mention}",
                color=discord.Color.green()
            )
            embed.set_footer(text="Giveaway ended • Use !reroll to reroll winners")
            await message.edit(embed=embed)
            
            # Announce winners
            winners_mentions = ', '.join([winner.mention for winner in winners])
            await channel.send(f"<a:giveaway:1426084232249212969> Congratulations {winners_mentions}! You won **{giveaway_info['prize']}**!")
            
            # Mark as ended
            giveaway_info['ended'] = True
            giveaway_info['winners'] = [w.id for w in winners]
            await self.save_config()
            print(f"[giveaway] ✅ Successfully ended giveaway {message_id} with {len(winners)} winner(s)")
            
        except Exception as e:
            print(f"[giveaway] ❌ Error ending giveaway {message_id}: {e}")
            import traceback
            traceback.print_exc()
            # Mark as ended even if there was an error to prevent infinite loops
            giveaway_info['ended'] = True
            await self.save_config()
            print(f"[giveaway] Marked giveaway {message_id} as ended due to error")
    
    @commands.command(name='reroll')
    async def reroll(self, ctx, message_id: int = None):
        """Reroll the winners of a giveaway (!reroll <message_id>)"""
        # Check permissions
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("<a:warning:1424944783587147868> You need 'Manage Messages' permission to use this command.")
            return
        
        # If no message ID provided, try to find the last giveaway in the channel
        if message_id is None:
            # Look for recent giveaways in this channel
            found = None
            async for message in ctx.channel.history(limit=50):
                if message.id in self.active_giveaways:
                    message_id = message.id
                    found = message
                    break
            
            if not found:
                await ctx.send("<a:warning:1424944783587147868> No recent giveaway found! Please provide a message ID: `!reroll <message_id>`")
                return
        
        # Check if giveaway exists
        if message_id not in self.active_giveaways:
            await ctx.send("<a:warning:1424944783587147868> That giveaway doesn't exist or has been deleted!")
            return
        
        giveaway_info = self.active_giveaways[message_id]
        
        # Check if giveaway has ended
        if not giveaway_info['ended']:
            await ctx.send("<a:warning:1424944783587147868> That giveaway hasn't ended yet!")
            return
        
        try:
            # Get the channel and message
            channel = self.bot.get_channel(giveaway_info['channel_id'])
            if not channel:
                await ctx.send("<a:warning:1424944783587147868> Giveaway channel not found!")
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.errors.NotFound:
                await ctx.send("<a:warning:1424944783587147868> Giveaway message not found!")
                return
            
            # Get users who reacted with the giveaway emoji
            reaction = None
            target_emoji_id = "1426084232249212969"  # The ID of the giveaway emoji
            for r in message.reactions:
                emoji_str = str(r.emoji)
                if target_emoji_id in emoji_str:
                    reaction = r
                    break
            
            if not reaction:
                await ctx.send("<a:warning:1424944783587147868> No reactions found on the giveaway!")
                return
            
            # Get all users who reacted (excluding bots)
            users = []
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
            
            if len(users) == 0:
                await ctx.send("<a:warning:1424944783587147868> No valid entries to reroll!")
                return
            
            # Pick new winners
            winners_count = min(giveaway_info['winners_count'], len(users))
            winners = random.sample(users, winners_count)
            
            # Create winners list
            winners_mention = '\n'.join([f"<a:trophy:1424944527315042415> {winner.mention}" for winner in winners])
            
            # Update embed
            embed = discord.Embed(
                title="<a:giveaway:1426084232249212969> GIVEAWAY REROLLED <a:giveaway:1426084232249212969>",
                description=f"**Prize:** {giveaway_info['prize']}\n\n"
                           f"**New Winner(s):**\n{winners_mention}",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Giveaway rerolled • Use !reroll to reroll again")
            await message.edit(embed=embed)
            
            # Announce new winners
            winners_mentions = ', '.join([winner.mention for winner in winners])
            await channel.send(f"🔄 New winner(s) rerolled! Congratulations {winners_mentions}! You won **{giveaway_info['prize']}**!")
            
            # Update stored winners
            giveaway_info['winners'] = [w.id for w in winners]
            await self.save_config()
            
            # Send confirmation in command channel if different
            if ctx.channel.id != channel.id:
                await ctx.send(f"✅ Giveaway rerolled successfully in {channel.mention}!")
            
        except Exception as e:
            await ctx.send(f"<a:warning:1424944783587147868> Error rerolling giveaway: {e}")
            print(f"[giveaway] Error rerolling giveaway {message_id}: {e}")
    
    async def _delayed_load_config(self):
        """Wait for database to be ready, then load config"""
        import asyncio
        
        # Wait for bot to be ready
        await self.bot.wait_until_ready()
        
        # Give database a moment to connect
        for attempt in range(10):
            await asyncio.sleep(0.5)
            
            # Re-get the database reference
            self.db = getattr(self.bot, 'db', None)
            
            if self.db and (self.db.is_postgres or self.db.is_sqlite):
                print(f"[giveaway] Database ready, loading config (attempt {attempt + 1})")
                await self.load_config()
                self._config_loaded = True
                return
            else:
                print(f"[giveaway] Database not ready yet, retrying... (attempt {attempt + 1}/10)")
        
        print("[giveaway] ❌ Database not available after 10 attempts, trying file fallback")
        # Fallback to file-based config
        self.load_config_from_file()
    
    def load_config_from_file(self):
        """Load giveaway configuration from file (fallback)"""
        try:
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    self.active_giveaways = {int(k): v for k, v in data.items()}
                    print(f"[giveaway] Loaded {len(self.active_giveaways)} giveaway(s) from file")
                    
                    # Restart timers for active giveaways
                    from datetime import timezone
                    for message_id, info in self.active_giveaways.items():
                        if not info['ended']:
                            end_time = datetime.fromisoformat(info['end_time'])
                            if end_time.tzinfo is None:
                                end_time = end_time.replace(tzinfo=timezone.utc)
                            now = datetime.now(timezone.utc)
                            if end_time > now:
                                seconds_remaining = (end_time - now).total_seconds()
                                asyncio.create_task(self._schedule_giveaway_end(message_id, seconds_remaining))
                            else:
                                asyncio.create_task(self.end_giveaway(message_id))
        except Exception as e:
            print(f"[giveaway] Error loading config from file: {e}")
            self.active_giveaways = {}
    
    async def load_config(self):
        """Load giveaway configuration from database"""
        if not self.db:
            print("[giveaway] Database not available, using file fallback")
            self.load_config_from_file()
            return
        
        # Check if database is actually connected
        if not (self.db.is_postgres or self.db.is_sqlite):
            print("[giveaway] Database not yet connected, using file fallback")
            self.load_config_from_file()
            return
        
        try:
            config = await self.db.get_config('giveaway_config')
            if config:
                # Convert string keys back to integers
                self.active_giveaways = {int(k): v for k, v in config.items()}
                print(f"[giveaway] Loaded {len(self.active_giveaways)} giveaway(s) from database")
                
                # Restart timers for active giveaways
                from datetime import timezone
                for message_id, info in self.active_giveaways.items():
                    if not info['ended']:
                        end_time = datetime.fromisoformat(info['end_time'])
                        if end_time.tzinfo is None:
                            end_time = end_time.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        if end_time > now:
                            # Schedule the giveaway to end
                            seconds_remaining = (end_time - now).total_seconds()
                            print(f"[giveaway] Restarting timer for giveaway {message_id}, {seconds_remaining:.0f}s remaining")
                            asyncio.create_task(self._schedule_giveaway_end(message_id, seconds_remaining))
                        else:
                            # Already past end time, end it now
                            print(f"[giveaway] Giveaway {message_id} already expired, ending now")
                            asyncio.create_task(self.end_giveaway(message_id))
            else:
                self.active_giveaways = {}
                print("[giveaway] No giveaway config found in database")
        except Exception as e:
            print(f"[giveaway] Error loading config from database: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to file
            self.load_config_from_file()
    
    async def save_config(self):
        """Save giveaway configuration to database"""
        # Try database first
        if self.db and (self.db.is_postgres or self.db.is_sqlite):
            try:
                # Convert integer keys to strings for JSON storage
                data = {str(k): v for k, v in self.active_giveaways.items()}
                await self.db.set_config('giveaway_config', data)
                print(f"[giveaway] Saved {len(self.active_giveaways)} giveaway(s) to database")
                return
            except Exception as e:
                print(f"[giveaway] Error saving config to database: {e}, falling back to file")
        
        # Fallback to file
        self.save_config_to_file()
    
    def save_config_to_file(self):
        """Save giveaway configuration to file (fallback)"""
        try:
            # Convert integer keys to strings for JSON
            data = {str(k): v for k, v in self.active_giveaways.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[giveaway] Saved {len(self.active_giveaways)} giveaway(s) to file")
        except Exception as e:
            print(f"[giveaway] Error saving config to file: {e}")
    
    async def _schedule_giveaway_end(self, message_id: int, seconds: float):
        """Schedule a giveaway to end after a delay"""
        print(f"[giveaway] Timer started for giveaway {message_id}, will end in {seconds:.0f} seconds")
        await asyncio.sleep(seconds)
        print(f"[giveaway] Timer expired for giveaway {message_id}, calling end_giveaway")
        await self.end_giveaway(message_id)


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
