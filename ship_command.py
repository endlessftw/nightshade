import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import random
import os


class ShipCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name='ship', description='Calculate relationship compatibility between two users')
    @app_commands.describe(
        user1='First user (leave empty to use yourself)',
        user2='Second user to ship with'
    )
    async def ship(
        self, 
        interaction: discord.Interaction, 
        user1: discord.Member = None,
        user2: discord.Member = None
    ):
        # Defer response since image generation takes time
        await interaction.response.defer()
        
        # If user1 is not provided, use the command author
        if user1 is None:
            user1 = interaction.user
        
        # user2 is required
        if user2 is None:
            await interaction.followup.send(
                "<a:warning:1424944783587147868> You need to mention at least one person to ship with!",
                ephemeral=True
            )
            return
        
        # Calculate compatibility (deterministic based on user IDs so it's consistent)
        compatibility = self.calculate_compatibility(user1.id, user2.id)
        
        try:
            # Download profile pictures
            user1_avatar = await self.get_avatar(user1)
            user2_avatar = await self.get_avatar(user2)
            
            # Generate ship image
            ship_image = await self.create_ship_image(user1_avatar, user2_avatar, compatibility)
            
            # Save to BytesIO
            image_buffer = io.BytesIO()
            ship_image.save(image_buffer, format='PNG')
            image_buffer.seek(0)
            
            # Create embed
            embed = discord.Embed(
                title="<:heart:1426125117972549703> Love Calculator <:heart:1426125117972549703>",
                description=f"**{user1.display_name}** 💕 **{user2.display_name}**",
                color=self.get_color_from_compatibility(compatibility)
            )
            
            embed.add_field(
                name="Compatibility",
                value=f"{self.get_compatibility_bar(compatibility)} **{compatibility}%**",
                inline=False
            )
            
            embed.add_field(
                name="Rating",
                value=self.get_compatibility_message(compatibility),
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            # Send the image
            file = discord.File(image_buffer, filename='ship.png')
            embed.set_image(url='attachment://ship.png')
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(
                f"<a:warning:1424944783587147868> Failed to create ship image: {e}",
                ephemeral=True
            )
            print(f"[ship] Error creating ship image: {e}")
    
    def calculate_compatibility(self, id1: int, id2: int):
        """Calculate compatibility percentage (deterministic based on IDs)"""
        # Sort IDs to ensure consistency regardless of order
        ids = sorted([id1, id2])
        # Use IDs as seed for consistent results
        random.seed(f"{ids[0]}{ids[1]}")
        compatibility = random.randint(0, 100)
        # Reset seed
        random.seed()
        return compatibility
    
    async def get_avatar(self, user: discord.Member):
        """Download user's avatar"""
        avatar_url = user.display_avatar.url
        
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    data = await response.read()
                    return Image.open(io.BytesIO(data)).convert('RGBA')
                else:
                    raise Exception(f"Failed to download avatar for {user.display_name}")
    
    async def create_ship_image(self, avatar1: Image.Image, avatar2: Image.Image, compatibility: int):
        """Create the ship image with two avatars and a heart"""
        # Image dimensions - made narrower to bring avatars closer
        width = 600
        height = 400
        avatar_size = 180
        
        # Create base image with gradient background
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Create gradient background
        gradient = self.create_gradient_background(width, height, compatibility)
        image.paste(gradient, (0, 0))
        
        # Resize and make avatars circular
        avatar1 = self.make_circular(avatar1.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS))
        avatar2 = self.make_circular(avatar2.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS))
        
        # Calculate positions - closer together
        avatar1_x = 30
        avatar2_x = width - avatar_size - 30
        avatar_y = (height - avatar_size) // 2 + 30
        
        # Paste avatars
        image.paste(avatar1, (avatar1_x, avatar_y), avatar1)
        image.paste(avatar2, (avatar2_x, avatar_y), avatar2)
        
        # Add plus symbol in the middle
        plus = self.create_plus(100, 100)
        plus_x = (width - 100) // 2
        plus_y = (height - 100) // 2 + 30
        image.paste(plus, (plus_x, plus_y), plus)
        
        # Add compatibility percentage at the top
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fall back to default if not available
        font_large = None
        font_small = None
        
        # Try multiple common font paths for different operating systems
        font_paths = [
            "arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        for font_path in font_paths:
            try:
                font_large = ImageFont.truetype(font_path, 80)
                font_small = ImageFont.truetype(font_path, 40)
                break
            except:
                continue
        
        # If no font found, use default
        if font_large is None:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw compatibility percentage
        percentage_text = f"{compatibility}%"
        
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), percentage_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        
        # Draw text with outline for better visibility
        outline_color = (0, 0, 0, 255)
        text_color = (255, 255, 255, 255)
        
        # Draw outline
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                draw.text((text_x + offset_x, 30 + offset_y), percentage_text, font=font_large, fill=outline_color)
        
        # Draw main text
        draw.text((text_x, 30), percentage_text, font=font_large, fill=text_color)
        
        return image
    
    def create_gradient_background(self, width: int, height: int, compatibility: int):
        """Create a gradient background based on compatibility"""
        image = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Choose colors based on compatibility
        if compatibility >= 75:
            color1 = (255, 105, 180)  # Hot pink
            color2 = (255, 20, 147)   # Deep pink
        elif compatibility >= 50:
            color1 = (255, 182, 193)  # Light pink
            color2 = (255, 105, 180)  # Hot pink
        elif compatibility >= 25:
            color1 = (173, 216, 230)  # Light blue
            color2 = (255, 182, 193)  # Light pink
        else:
            color1 = (128, 128, 128)  # Gray
            color2 = (169, 169, 169)  # Dark gray
        
        # Create gradient
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
        return image
    
    def make_circular(self, image: Image.Image):
        """Make an image circular"""
        size = image.size
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def create_plus(self, width: int, height: int):
        """Create a nice-looking plus symbol"""
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Plus color (pink/magenta)
        color = (255, 255, 255, 255)  # White
        outline_color = (255, 20, 147, 255)  # Deep pink
        shadow_color = (0, 0, 0, 80)  # Semi-transparent black for shadow
        
        center_x = width // 2
        center_y = height // 2
        
        # Plus dimensions - rounded ends
        plus_thickness = int(width * 0.25)
        plus_length = int(width * 0.8)
        
        # Calculate corner radius for rounded rectangles
        corner_radius = plus_thickness // 2
        
        # Draw shadow (offset slightly)
        shadow_offset = 3
        
        # Horizontal bar shadow
        draw.rounded_rectangle(
            [center_x - plus_length // 2 + shadow_offset, 
             center_y - plus_thickness // 2 + shadow_offset,
             center_x + plus_length // 2 + shadow_offset, 
             center_y + plus_thickness // 2 + shadow_offset],
            radius=corner_radius,
            fill=shadow_color
        )
        
        # Vertical bar shadow
        draw.rounded_rectangle(
            [center_x - plus_thickness // 2 + shadow_offset, 
             center_y - plus_length // 2 + shadow_offset,
             center_x + plus_thickness // 2 + shadow_offset, 
             center_y + plus_length // 2 + shadow_offset],
            radius=corner_radius,
            fill=shadow_color
        )
        
        # Draw horizontal bar (with outline)
        draw.rounded_rectangle(
            [center_x - plus_length // 2, 
             center_y - plus_thickness // 2,
             center_x + plus_length // 2, 
             center_y + plus_thickness // 2],
            radius=corner_radius,
            fill=color,
            outline=outline_color,
            width=3
        )
        
        # Draw vertical bar (with outline)
        draw.rounded_rectangle(
            [center_x - plus_thickness // 2, 
             center_y - plus_length // 2,
             center_x + plus_thickness // 2, 
             center_y + plus_length // 2],
            radius=corner_radius,
            fill=color,
            outline=outline_color,
            width=3
        )
        
        return image
    
    def get_color_from_compatibility(self, compatibility: int):
        """Get embed color based on compatibility"""
        if compatibility >= 75:
            return discord.Color.from_rgb(255, 20, 147)  # Deep pink
        elif compatibility >= 50:
            return discord.Color.from_rgb(255, 105, 180)  # Hot pink
        elif compatibility >= 25:
            return discord.Color.from_rgb(173, 216, 230)  # Light blue
        else:
            return discord.Color.from_rgb(128, 128, 128)  # Gray
    
    def get_compatibility_bar(self, compatibility: int):
        """Create a visual bar for compatibility"""
        filled = int(compatibility / 10)
        empty = 10 - filled
        return '💖' * filled + '🖤' * empty
    
    def get_compatibility_message(self, compatibility: int):
        """Get a message based on compatibility"""
        if compatibility >= 90:
            return "💕 Perfect Match! You two are meant to be together!"
        elif compatibility >= 75:
            return "💗 Great Match! You two would make a lovely couple!"
        elif compatibility >= 60:
            return "💓 Good Match! There's definitely potential here!"
        elif compatibility >= 40:
            return "💛 Decent Match! Could work with some effort!"
        elif compatibility >= 25:
            return "💙 Low Match! Maybe just friends?"
        else:
            return "💔 Poor Match! Better luck next time!"


async def setup(bot: commands.Bot):
    await bot.add_cog(ShipCog(bot))
