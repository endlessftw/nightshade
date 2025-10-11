import random
import discord
from discord.ext import commands
from discord import app_commands


SHADOW_TITLES = [
    "Bearer of Midnight Flame",
    "Whisperer of Forgotten Echoes",
    "Warden of the Veiled Crescent",
    "Keeper of the Obsidian Sigil",
    "Harbinger of Quiet Storms",
    "Glimmer in the Hollow Night",
    "Sovereign of Sable Winds",
    "Starlit Shade of the Abyss",
    "Emissary of Silent Thunder",
    "Seeker of Moonless Paths",
    "Lord of the Dimming Light",
    "Mistress of the Hidden Ember",
    "Architect of the Last Dawn",
    "Shadow of the Falling Star",
    "Wraith of the Silvered Vale",
    "Oracle of the Hollow Lantern",
    "Reaper of Quiet Promises",
    "Pilgrim of the Deep Hush",
    "Nomad of the Starless Expanse",
    "Chronicler of Midnight Oaths",
    "Vanguard of the Umbral Gate",
    "Singer of Forgotten Names",
    "Guardian of the Nightbound Oath",
    "Phantom of the Distant Hearth",
    "Voyager through Shadowed Seas",
    "Bearer of the Eclipsed Crown",
    "Weaver of Dusk's Thread",
    "Left-Hand of the Quiet Throne",
    "Child of the Waning Light",
    "Heir to the Silent Ember",
    "Sentinel of the Veiled Road",
    "Warden of the Ashen Keeps",
    "Bearer of the Last Candle",
    "Knight of the Hollow Vigil",
    "Bearer of the Night's Lament",
    "Scholar of the Moon's Remorse",
    "Rider of the Pale Horizon",
    "Keeper of the Stormless Sea",
    "Librarian of Forgotten Tomes",
    "Watcher Beyond the Quiet Gate",
    "Caller of Soft Cataclysms",
    "Bearer of Midnight's Promise",
    "Voice from the Velvet Deep",
    "Seamstress of Broken Constellations",
    "Patron of the Waning Hour",
    "Bard of the Hollowed Hearth",
    "Hunter of the Silent Bloom",
    "Shade of the Passing Bell",
    "Warden of the Moonless Dock",
]


class ShadowCog(commands.Cog):
    """Gives a dramatic shadow title for a user."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shadow", description="Give someone a dramatic 'shadow' title.")
    @app_commands.describe(target="(optional) target user to give a shadow title to")
    async def shadow(self, interaction: discord.Interaction, target: discord.User = None):
        who = target or interaction.user
        # pick a title
        title = random.choice(SHADOW_TITLES)
        # Bold the name and title
        content = f"**{who.display_name}, the {title}**"
        await interaction.response.send_message(content)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShadowCog(bot))
