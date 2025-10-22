import discord
from discord.ext import commands
from discord import app_commands
import random


class TruthOrDareCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Truth questions
        self.truths = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?",
            "Who was your first crush?",
            "What's the worst lie you've ever told?",
            "What's something you've never told anyone?",
            "What's the most childish thing you still do?",
            "What's your worst habit?",
            "Have you ever cheated on a test?",
            "What's the last thing you searched on your phone?",
            "What's your biggest insecurity?",
            "Who do you have a secret crush on?",
            "What's the most trouble you've been in?",
            "What's something you're glad your parents don't know about?",
            "Have you ever lied to your best friend?",
            "What's the meanest thing you've ever said to someone?",
            "What's something illegal you've done?",
            "What's your most embarrassing moment at school?",
            "Have you ever broken something and blamed someone else?",
            "What's the longest you've gone without showering?",
            "What's the weirdest dream you've ever had?",
            "Have you ever stalked someone on social media?",
            "What's something you've done that you still regret?",
            "Who's the last person you creeped on social media?",
            "What's a secret you've kept from your parents?",
            "Have you ever had a crush on someone in this server?",
            "What's the most embarrassing thing in your room?",
            "What's the silliest thing you believed as a child?",
            "What's the weirdest thing you've ever eaten?",
            "Have you ever pretended to be sick to skip school?",
            "What's the most ridiculous outfit you've ever worn?",
            "You have to relive one embarrassing moment from your past once a week for the rest of your life. Which one do you choose?",
            "You can know the exact date and time of your death, but you can't change it. Do you want to know?",
            "If you could read minds but only your family's minds, would you do it knowing you can't turn it off?",
            "If you had to eat a crayon, what color would you choose and why?",
            "If you could swap lives with any fictional character for a day, who would it be?",
            "What's the most embarrassing thing you've done in front of a crush?",
            "Have you ever sent a text to the wrong person? What did it say?",
            "What's the weirdest nickname you've ever had?",
            "If you could only listen to one song for the rest of your life, what would it be?",
            "What's the most embarrassing thing you've ever posted online?",
            "If you had to wear one Halloween costume every day for a year, what would it be?",
            "What's the most ridiculous thing you've convinced someone to believe?",
            "If you could have any superpower, but it had to be completely useless, what would it be?",
            "What's the funniest way you've been injured?",
            "What's the most embarrassing thing you've done while trying to impress someone?",
            "What's the most ridiculous thing you've done on a dare?",
            "You wake up with the ability to speak every language, but you forget your native language. Would you make that trade?",
            "If you could only eat one food for the rest of your life, what would it be?",
            "What's the most interesting thing you've learned recently?",
            "What's the most surprising thing you've discovered about yourself?",
            "If you could live in any fictional universe, which one would you choose?",
            "If aliens made contact tomorrow and offered to take 100 humans to live on their perfect planet, would you volunteer to go knowing you'd never return?",
            "If you could live forever but everyone you ever loved would still die normally, would you choose immortality?",
            "You're offered $10 million but you have to spend one year completely alone in a comfortable room with no contact with anyone. Do you take it?",
            "If you could make one person disappear from your life with no consequences and no one would remember them, who would it be and why?",
            "If you had to choose between saving your pet or a stranger's child from a burning building, what would you honestly do?",
            "What's a compliment someone gave you that you secretly know was a lie?",
            "If you could swap lives with someone you know for a year, whose life would you take and why?",
            "You can become the most successful person in your field, but you'll never feel satisfied or happy. Do you take it?",
            "If you could remove one emotion from yourself permanently (love, fear, anger, sadness, jealousy), which would you choose?",
            "If you had to choose between being loved by everyone but never loving anyone, or loving everyone but never being loved, which do you choose?",
            "You can cure world hunger but you have to sacrifice your five closest relationships. Do you do it?",
            "If you could experience the single happiest moment of your life on repeat forever, would you give up the rest of your life to do it?",
            "You can make everyone forget you ever existed, including yourself, and get a completely fresh start. Do you press the button?",
            "If you could commit one crime with zero consequences and no one would ever know, what would it be?",
            "If you had to haunt one person as a ghost for eternity, who would you choose and how would you mess with them?",
            "What's something you've said 'as a joke' that was actually 100% how you really felt?",
            "If you could instantly know the truth behind one mystery, what mystery would you choose?",
            "If everyone in this room was in a zombie apocalypse, rank the order you think they'd die in.",
            "If you had to roast everyone here in order from easiest to hardest, what would the order be?",
            "What's something you've pretended to like to fit in with a group?",
            "Who do you talk about the most behind their back, and what do you usually say?",
            "If you had to date someone in this room for a year for $100,000, who would make it the easiest?",
            "If you could cancel one popular thing that everyone loves (movie, artist, trend), what would it be just to watch the chaos?",
            "If you could witness any moment in your parents' lives before you were born, what would you want to see?",
            "Would you rather fight 100 duck-sized versions of your worst enemy or one horse-sized version of your most annoying coworker?",
            "You have to give up either music or TV shows/movies for the rest of your life, which do you choose?",
            "What's something you're addicted to that people wouldn't guess?",
            "If you could make everyone see themselves the way you see them, who would be most shocked?",
            "What's something you do when you're alone that would completely change how people see you?",
            "If you had to describe yourself using only the search history you'd be most embarrassed about, what would we learn?",
            "If you had to sacrifice one person to save the rest of humanity, how would you decide who?",
            "You can either speak to animals but they're all brutally honest and mean, or read people's minds but only their worst thoughts about you, which curse do you pick?",
        ]
        
        # Dare challenges
        self.dares = [
            "Send a screenshot of your search history.",
            "Let someone go through your phone for 1 minute.",
            "Post an embarrassing photo of yourself.",
            "Do 20 pushups and post a video.",
            "Send a voice message singing your favorite song.",
            "Change your status to something embarrassing for 1 hour.",
            "Let the group choose your profile picture for 24 hours.",
            "Text your crush and tell them how you feel.",
            "Post 'I love pineapple on pizza' in the chat.",
            "Do your best impression of someone in the server.",
            "Speak in an accent for the next 10 minutes.",
            "Share your most embarrassing photo.",
            "Let someone send a message from your account.",
            "Post a video of you doing a TikTok dance.",
            "Call someone random and sing 'Happy Birthday'.",
            "Change your nickname to whatever the group chooses.",
            "Send a funny selfie with a weird filter.",
            "Tell a bad joke in the chat.",
            "Do 10 jumping jacks on camera.",
            "Share your most played song.",
            "Let someone read your last 5 DMs.",
            "Post your most used emoji 20 times.",
            "Make your discord status 'I smell bad' for 30 minutes.",
            "Voice chat and talk like a robot for 2 minutes.",
            "Send a message to someone saying 'You're amazing!' randomly.",
            "Change your profile picture to an embarrassing childhood photo for 24 hours.",
            "Let someone else write your status/bio for the next hour.",
            "Do your best impression of someone in this server.",
            "Post an embarrassing story about yourself in the chat.",
            "Share the most embarrassing song in your playlist.",
            "Talk in rhymes for the next 5 minutes.",
            "Post a weird selfie and don't delete it for 1 hour.",
            "Compliment everyone in the chat in the most over-the-top way possible.",
            "Beatbox for 30 seconds.",
            "Speak only in questions for the next 5 minutes.",
            "Do your best celebrity impression.",
            "Send a text to your 5th contact saying 'I know what you did' then immediately say just kidding.",
            "Pretend you're a news anchor and report on what's happening in the chat.",
            "Rap the next thing you say.",
            "Yell out the window 'I love Discord!'.",
            "Speak in a British accent for the next 10 minutes.",
            "Put on socks on your hands for the next 5 minutes.",
            "Do 30 seconds of your best freestyle rap.",
            "Act like a robot for 2 minutes.",
            "Do your worst impression of your favorite teacher.",
            "Speak only in movie quotes for 5 minutes.",
        ]
    
    @app_commands.command(name='truthordare', description='Play Truth or Dare!')
    async def truthordare(self, interaction: discord.Interaction):
        """Start a game of Truth or Dare"""
        # Get a random truth question
        truth = random.choice(self.truths)
        
        # Create embed
        embed = discord.Embed(
            description=f"**{truth}**",
            color=discord.Color.blue()
        )
        embed.set_author(name=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Click a button to get a new Truth or Dare!")
        
        # Create view with buttons
        view = TruthOrDareView(self.truths, self.dares)
        
        await interaction.response.send_message(embed=embed, view=view)


class TruthOrDareView(discord.ui.View):
    def __init__(self, truths: list, dares: list):
        super().__init__(timeout=300)  # 5 minute timeout
        self.truths = truths
        self.dares = dares
    
    @discord.ui.button(label="Truth", style=discord.ButtonStyle.green, emoji="💬")
    async def truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Truth button click"""
        truth = random.choice(self.truths)
        
        embed = discord.Embed(
            description=f"**{truth}**",
            color=discord.Color.green()
        )
        embed.set_author(name=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Click a button to get a new Truth or Dare!")
        
        # Create a new view for the new message
        new_view = TruthOrDareView(self.truths, self.dares)
        
        # Send a new message instead of editing
        await interaction.response.send_message(embed=embed, view=new_view)
    
    @discord.ui.button(label="Dare", style=discord.ButtonStyle.red, emoji="🔥")
    async def dare_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Dare button click"""
        dare = random.choice(self.dares)
        
        embed = discord.Embed(
            description=f"**{dare}**",
            color=discord.Color.red()
        )
        embed.set_author(name=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Click a button to get a new Truth or Dare!")
        
        # Create a new view for the new message
        new_view = TruthOrDareView(self.truths, self.dares)
        
        # Send a new message instead of editing
        await interaction.response.send_message(embed=embed, view=new_view)


async def setup(bot: commands.Bot):
    await bot.add_cog(TruthOrDareCog(bot))
