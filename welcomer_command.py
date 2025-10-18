import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont # type: ignore
import aiohttp
from io import BytesIO


class WelcomerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = getattr(bot, 'db', None)
        # Dictionary to store {guild_id: channel_id} for welcome channels (cached in memory)
        self.welcome_channels = {}
        # Load saved welcome channels from database
        self.bot.loop.create_task(self.load_config())
    
    @app_commands.command(name='welcomer', description='Set up a welcome channel for new members')
    @app_commands.describe(channel='The channel where welcome messages will be sent')
    async def welcomer(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # Check if user has permission to manage channels
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("<a:warning:1424944783587147868> You need 'Manage Channels' permission to use this command.", ephemeral=True)
            return
        
        # Store the welcome channel for this guild
        self.welcome_channels[interaction.guild.id] = channel.id
        
        # Save to database
        await self.save_config()
        
        await interaction.response.send_message(
            f"✅ Welcome channel set to {channel.mention}!\nNew members will receive a welcome message there.",
            ephemeral=True
        )
    
    async def load_config(self):
        """Load welcome channel configuration from database"""
        if not self.db:
            print("[welcomer] Database not available, using empty config")
            self.welcome_channels = {}
            return
        
        try:
            config = await self.db.get_config('welcomer_config')
            if config:
                # Convert string keys back to integers
                self.welcome_channels = {int(k): int(v) for k, v in config.items()}
                print(f"[welcomer] Loaded {len(self.welcome_channels)} welcome channel(s) from database")
            else:
                self.welcome_channels = {}
                print("[welcomer] No welcomer config found in database")
        except Exception as e:
            print(f"[welcomer] Error loading config from database: {e}")
            self.welcome_channels = {}
    
    async def save_config(self):
        """Save welcome channel configuration to database"""
        if not self.db:
            print("[welcomer] Database not available, cannot save config")
            return
        
        try:
            # Convert integer keys to strings for JSON storage
            data = {str(k): v for k, v in self.welcome_channels.items()}
            await self.db.set_config('welcomer_config', data)
            print(f"[welcomer] Saved configuration to database")
        except Exception as e:
            print(f"[welcomer] Error saving config to database: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Check if this guild has a welcome channel set
        channel_id = self.welcome_channels.get(member.guild.id)
        if not channel_id:
            return
        
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        
        try:
            # Create the welcome image
            welcome_image = await self.create_welcome_image(member)
            
            # Send the welcome message
            file = discord.File(welcome_image, filename="welcome.png")
            await channel.send(f"<a:wave:1425776109340987475> Welcome {member.mention} to **{member.guild.name}**!", file=file)
        except Exception as e:
            print(f"[welcomer] Error creating welcome image: {e}")
            # Fallback to text-only welcome
            await channel.send(f"<a:wave:1425776109340987475> Welcome {member.mention} to **{member.guild.name}**! 🎉")
    
    async def create_welcome_image(self, member: discord.Member):
        """Create a welcome image with the member's avatar and server info"""
        # Get the banner image path
        banner_path = os.path.join(os.path.dirname(__file__), "nightshadebannertwo.png")
        
        # Load the banner image
        if os.path.isfile(banner_path):
            banner = Image.open(banner_path).convert("RGBA")
        else:
            # Create a default banner if file doesn't exist
            banner = Image.new("RGBA", (1200, 400), (47, 49, 54, 255))
        
        # Resize banner to standard size
        banner = banner.resize((1200, 400), Image.Resampling.LANCZOS)
        
        # Download the member's avatar
        avatar_url = member.display_avatar.url
        async with aiohttp.ClientSession() as session:
            async with session.get(str(avatar_url)) as resp:
                avatar_data = await resp.read()
        
        avatar = Image.open(BytesIO(avatar_data)).convert("RGBA")
        
        # Resize avatar to circular profile picture (200x200)
        avatar = avatar.resize((200, 200), Image.Resampling.LANCZOS)
        
        # Create circular mask for avatar
        mask = Image.new("L", (200, 200), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 200, 200), fill=255)
        
        # Apply circular mask to avatar
        circular_avatar = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        circular_avatar.paste(avatar, (0, 0))
        circular_avatar.putalpha(mask)
        
        # Create a new image for compositing
        final_image = Image.new("RGBA", (1200, 400), (0, 0, 0, 0))
        final_image.paste(banner, (0, 0))
        
        # Paste the circular avatar on the left side
        avatar_x = 50
        avatar_y = 100
        final_image.paste(circular_avatar, (avatar_x, avatar_y), circular_avatar)
        
        # Add text on the right side
        draw = ImageDraw.Draw(final_image)
        
        # Try to load a nice font, fallback to default if not available
        try:
            # Try different font paths (Windows, Linux, Mac)
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (Debian/Ubuntu)
                "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",           # Linux (RHEL/CentOS)
                "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",   # Linux alternative
                "C:/Windows/Fonts/arial.ttf",                            # Windows
                "C:/Windows/Fonts/segoeui.ttf",                          # Windows
                "/System/Library/Fonts/Helvetica.ttc",                   # macOS
            ]
            font = None
            small_font = None
            for font_path in font_paths:
                if os.path.isfile(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 60)        # Increased from 50
                        small_font = ImageFont.truetype(font_path, 45)  # Increased from 35
                        break
                    except Exception:
                        continue
            
            # Fallback: use default font with size if available (Pillow 10+)
            if font is None:
                try:
                    font = ImageFont.load_default(size=60)
                    small_font = ImageFont.load_default(size=45)
                except TypeError:
                    # Older Pillow version - size parameter not supported
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
        except Exception:
            try:
                font = ImageFont.load_default(size=60)
                small_font = ImageFont.load_default(size=45)
            except TypeError:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Text position (right side of the avatar)
        text_x = 300
        text_y = 120
        
        # Draw "Welcome" text
        welcome_text = "Welcome"
        draw.text((text_x, text_y), welcome_text, fill=(255, 255, 255), font=font)
        
        # Draw member name
        member_name = member.display_name
        if len(member_name) > 20:
            member_name = member_name[:20] + "..."
        draw.text((text_x, text_y + 60), member_name, fill=(88, 101, 242), font=font)
        
        # Draw "to [server name]"
        server_name = member.guild.name
        if len(server_name) > 25:
            server_name = server_name[:25] + "..."
        to_text = f"to {server_name}"
        draw.text((text_x, text_y + 120), to_text, fill=(200, 200, 200), font=small_font)
        
        # Add total member count on the right side
        member_count = member.guild.member_count
        
        # Position for member count (far right)
        count_x = 850
        count_y = 150
        
        # Draw total server count
        total_text = f"Total: {member_count}"
        draw.text((count_x, count_y), total_text, fill=(88, 101, 242), font=font)
        
        # Save to BytesIO
        output = BytesIO()
        final_image = final_image.convert("RGB")  # Convert to RGB for saving as PNG
        final_image.save(output, format="PNG")
        output.seek(0)
        
        return output


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomerCog(bot))
