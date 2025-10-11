import io
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands


class AuraCommand(commands.Cog):
    """Create a white canvas and paste the user's avatar onto it, send as an inline image."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _fetch_avatar_bytes(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()

    @app_commands.command(name="aura", description="Create a canvas showing a user's aura. Defaults to yourself if no user is provided.")
    @app_commands.describe(target="The user whose aura to check (optional)")
    async def aura(self, interaction: discord.Interaction, target: discord.User = None):
        # If no target is provided, default to the invoking user
        user = target or interaction.user
        avatar_url = user.display_avatar.replace(size=512).url

        await interaction.response.defer(ephemeral=False)

        try:
            content = await self._fetch_avatar_bytes(avatar_url)
        except Exception as e:
            await interaction.followup.send(f"Failed to fetch avatar: {e}")
            return

        try:
            # Lazy import Pillow so the module can import even if Pillow isn't installed.
            from PIL import Image
        except Exception:
            await interaction.followup.send(
                "Pillow library is not installed. Install it with: `pip install Pillow`",
            )
            return

        try:
            avatar = Image.open(io.BytesIO(content)).convert("RGBA")
        except Exception as e:
            await interaction.followup.send(f"Failed to open avatar image: {e}")
            return

        # Create a rectangular layout: avatar on the left, aura bar on the right
        canvas_width, canvas_height = 700, 240
        # Use a Discord-dark background so the avatar and aura bar sit on a darker canvas
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (54, 57, 63, 255))

        # Resize avatar to fit in left area
        avatar_size = 200
        avatar = avatar.copy()
        avatar.thumbnail((avatar_size, avatar_size), Image.LANCZOS)

        # Create a circular mask for the avatar
        mask = Image.new("L", avatar.size, 0)
        from PIL import ImageDraw
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)

        # Position avatar with some left padding and centered vertically
        left_pad = 20
        av_x = left_pad
        av_y = (canvas_height - avatar.size[1]) // 2
        canvas.paste(avatar, (av_x, av_y), mask)

        # Draw the aura bar on the right side
        draw = ImageDraw.Draw(canvas)
        bar_width = 440
        bar_height = 160
        bar_x0 = canvas_width - bar_width - 30
        bar_y0 = (canvas_height - bar_height) // 2
        bar_x1 = bar_x0 + bar_width
        bar_y1 = bar_y0 + bar_height

        # Deterministic fill percentage based on the user's ID so repeated calls produce the same result
        try:
            uid = int(user.id)
        except Exception:
            # Fallback to hashing the string representation
            import hashlib
            uid_hash = hashlib.sha256(str(user.id).encode()).hexdigest()
            uid = int(uid_hash[:8], 16)

        # Reduce to 0..100
        percent = uid % 101

         # Background of the bar (empty part) drawn with rounded corners for a sleeker look
        radius = 18
        draw.rounded_rectangle([bar_x0, bar_y0, bar_x1, bar_y1], radius=radius, fill=(240, 240, 240), outline=(200, 200, 200))


        # Filled portion (left to right) as a rounded rectangle; adapt radius for small fills
        fill_inner_width = bar_width - 8  # account for inner padding
        fill_pixels = int(fill_inner_width * (percent / 100.0))
        # Use a color scale: green when >66, orange when 33-66, red when <33
        if percent > 66:
            fill_color = (75, 181, 67)  # green
        elif percent > 33:
            fill_color = (245, 166, 35)  # orange
        else:
            fill_color = (220, 75, 75)  # red

        inner_left = bar_x0 + 4
        inner_top = bar_y0 + 4
        inner_bottom = bar_y1 - 4
        inner_right = inner_left + fill_pixels

        # Only draw if there is at least 2px width
        if fill_pixels > 2:
            # radius for the filled rect should not exceed half the width to avoid visual artifacts
            fill_radius = min(radius, max(0, (inner_right - inner_left) // 2))
            draw.rounded_rectangle([inner_left, inner_top, inner_right, inner_bottom], radius=fill_radius, fill=fill_color)

        # Draw percentage text on top of the bar (centered). Use stroke for visibility
        try:
            from PIL import ImageFont
            font_size = 28
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        except Exception:
            # Fallback if PIL.ImageFont import fails for some reason
            from PIL import ImageFont as _IF
            font = _IF.load_default()
            font_size = 14

        text = f"{percent}%"
        # Measure text size (use textbbox when available)
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            try:
                text_width, text_height = font.getsize(text)
            except Exception:
                text_width, text_height = (50, 20)

        # Center the text horizontally over the whole bar, vertically centered in the bar
        text_x = bar_x0 + (bar_width - text_width) // 2
        text_y = bar_y0 + (bar_height - text_height) // 2

        stroke_w = max(1, font_size // 12)
        # Prefer draw.text stroke parameters when available (Pillow >= 8.0); fallback to manual outline
        try:
            draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
        except TypeError:
            # Manual outline for older Pillow
            outline_color = (0, 0, 0)
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                draw.text((text_x + ox, text_y + oy), text, font=font, fill=outline_color)
            draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

        # Save to bytes
        buf = io.BytesIO()
        canvas.convert("RGB").save(buf, format="PNG")
        buf.seek(0)

        file = discord.File(fp=buf, filename="aura.png")
        # white() is not available on discord.Color; use from_rgb instead
        embed = discord.Embed(title=f"{user.display_name}'s Aura <a:aura:1424658904918528084>", color=discord.Color.from_rgb(255, 255, 255))
        embed.set_image(url="attachment://aura.png")

        await interaction.followup.send(file=file, embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AuraCommand(bot))
