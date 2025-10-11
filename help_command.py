import os
import discord
from discord.ext import commands
from discord import app_commands

MODERATION_COMMANDS = [
    ("<:banhammer:1426111097005539371> /ban", "Ban a user from the server."),
    ("<:kick:1426111903037390979> /kick", "Kick a user from the server."),
    ("<:timeout:1426116778395828244> /timeout", "Temporarily timeout a user."),
    ("<:unmute:1426118353063248005> /untimeout", "Remove timeout from a user."),
    ("<:profile:1426112264964018187> /userprofile", "Show detailed information about a user."),
    ("<a:warn:1426420218518835263> /warn", "Warn a user for breaking rules."),
    ("<a:warn:1426420218518835263> /unwarn", "Remove a warning from a user."),
    ("<a:warn:1426420218518835263> /clearwarnings", "Clear all warnings of a user."),
    ("<a:warn:1426420218518835263> /warnings", "View warnings for a user."),
]

UTILITY_COMMANDS = [
    ("<a:phone:1424654842491834449> /userphone", "Join the userphone queue or start connecting channels for anonymous cross-server chat."),
    ("<a:phone:1424654842491834449> /hangup", "End a current userphone call you started, or stop waiting in the queue."),
    ("<:profile:1424652512081739866> /myprofile", "Show your userphone stats: messages relayed and userphones started."),
    ("<a:clock:1424650341651189772> /timezone", "Get the current time for a nations capital."),
    ("<a:clock:1424655674142363668> /timechannel", "Post a live-updating embed showing the chosen capitals local time."),
    ("<a:ping:1424656851173113937> /ping", "Show bot websocket latency and measured response RTT."),
    ("<a:quote:1424658219703205928> /quote", "Get a random inspirational quote."),
    ("<:reddit:1425747116818694164> /askreddit", "Get a random question from Reddits AskReddit subreddit."),
    ("<a:music:1425403164688908299> /play", "Play audio from a YouTube URL or search term in your current voice channel."),
    ("<a:wave:1425776109340987475> /welcomer", "Set a channel to receive welcome messages and images for new members."),
    ("<a:giveaway:1426084232249212969> /giveaway", "Start a giveaway in your server to give away prizes to random participants."),
]

GAME_COMMANDS = [
    ("<a:tictactoe:1424942287070433342> /tictactoe", "Challenge someone to a Tic-Tac-Toe match."),
    ("<a:connectfour:1425036938984947712> /connectfour", "Challenge someone to a Connect Four match."),
    ("<a:rockpaperscissor:1425347479389470720> /rockpaperscissors", "Challenge someone to a Rock-Paper-Scissors match."),
    ("<:hangpepe:1425770634415444028> /hangman", "Play Hangman - guess the word letter by letter! Play solo or challenge a friend."),
    ("<a:8ball:1424657451038539806> /8ball", "Ask the magic 8-ball a question; the bot replies with a playful answer."),
    ("<a:aura:1424658904918528084> /aura", "Create a visual aura image for a user."),
    ("<a:coin:1424668396573691906> /coin", "Flip a coin, get either heads or tails."),
    ("<:shadow:1424660147623694447> /shadow", "Create a shadow name for yourself or a user."),
    ("<:heart:1426125117972549703> /ship", "Calculate the relationship compatibility between two users."),
    ("<a:sniper:1425275162894532659> /snipe", "Expose the last deleted message in the current channel."),
]


class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.danger)
    async def moderation_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="<:shield:1425769315873067018> Moderation Commands <:shield:1425769315873067018>",
            description="Commands for server moderation and management.",
            color=discord.Color.red()
        )
        
        if MODERATION_COMMANDS:
            for name, desc in MODERATION_COMMANDS:
                embed.add_field(name=name, value=desc, inline=False)
        else:
            embed.description = "No moderation commands available yet."
        
        embed.set_footer(text="Created by s1lv3rsurf3r")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Utilities", style=discord.ButtonStyle.primary)
    async def utilities_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="<:tools:1425768546343977031> Utility Commands <:tools:1425768546343977031>",
            description="Useful commands for various purposes.",
            color=discord.Color.blue()
        )
        
        for name, desc in UTILITY_COMMANDS:
            embed.add_field(name=name, value=desc, inline=False)
        
        embed.set_footer(text="Created by s1lv3rsurf3r")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Games", style=discord.ButtonStyle.success)
    async def games_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="<a:controller:1425767487487738001> Game Commands <a:controller:1425767487487738001>",
            description="Fun games to play with friends!",
            color=discord.Color.green()
        )
        
        for name, desc in GAME_COMMANDS:
            embed.add_field(name=name, value=desc, inline=False)
        
        embed.set_footer(text="Created by s1lv3rsurf3r")
        await interaction.response.edit_message(embed=embed, view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show bot commands and explanations.")
    async def help(self, interaction: discord.Interaction):
        banner_path = os.path.join(os.path.dirname(__file__), "nightshadebannertwo.png")
        
        embed = discord.Embed(
            title="NightShade Bot",
            description="**Welcome to NightShade!**\n\nNightShade is a multi-purpose Discord bot featuring games, utilities, and fun commands!\n\n**Choose a category below to explore commands:**",
            color=discord.Color.blurple(),
        )
        
        
        view = CategoryView()
        
        try:
            if os.path.isfile(banner_path):
                file = discord.File(banner_path, filename="nightshadebannertwo.png")
                await interaction.response.send_message(file=file, embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        except discord.HTTPException as e:
            print(f"[help] HTTPException: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, view=view)
                else:
                    await interaction.followup.send(embed=embed, view=view)
            except Exception as e2:
                print(f"[help] Fallback failed: {e2}")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message("Failed to load help menu.", ephemeral=True)
                except Exception:
                    pass
        except Exception as e:
            print(f"[help] Unexpected error: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("An error occurred while loading the help menu.", ephemeral=True)
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
