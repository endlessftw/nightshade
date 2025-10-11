import random
import discord
from discord.ext import commands
from discord import app_commands

QUOTES = [
    "The only limit to our realization of tomorrow is our doubts of today. — **Franklin D. Roosevelt**",
    "In the middle of every difficulty lies opportunity. — **Albert Einstein**",
    "The best way to predict the future is to invent it. — **Alan Kay**",
    "Do not wait to strike till the iron is hot; but make it hot by striking. — **William Butler Yeats**",
    "Life is 10% what happens to us and 90% how we react to it. — **Charles R. Swindoll**",
    "The mind is everything. What you think you become. — **Buddha**",
    "The only way to do great work is to love what you do. — **Steve Jobs**",
    "If you can dream it, you can do it. — **Walt Disney**",
    "The journey of a thousand miles begins with one step. — **Lao Tzu**",
    "You miss 100% of the shots you don't take. — **Wayne Gretzky**",
    "It does not matter how slowly you go as long as you do not stop. — **Confucius**",
    "Keep your face always toward the sunshine—and shadows will fall behind you. — **Walt Whitman**",
    "What lies behind us and what lies before us are tiny matters compared to what lies within us. — **Ralph Waldo Emerson**",
    "Whether you think you can or you think you can't, you're right. — **Henry Ford**",
    "The only impossible journey is the one you never begin. — **Tony Robbins**",
    "Act as if what you do makes a difference. It does. — **William James**",
    "Happiness is not something ready made. It comes from your own actions. — **Dalai Lama**",
    "Believe you can and you're halfway there. — **Theodore Roosevelt**",
    "A person who never made a mistake never tried anything new. — **Albert Einstein**",
    "Success usually comes to those who are too busy to be looking for it. — **Henry David Thoreau**",
    "Don't watch the clock; do what it does. Keep going. — **Sam Levenson**",
    "Start where you are. Use what you have. Do what you can. — **Arthur Ashe**",
    "The power of imagination makes us infinite. — **John Muir**",
    "You are never too old to set another goal or to dream a new dream. — **C.S. Lewis**",
    "Everything you've ever wanted is on the other side of fear. — **George Addair**",
    "The future belongs to those who believe in the beauty of their dreams. — **Eleanor Roosevelt**",
    "Don't be afraid to give up the good to go for the great. — **John D. Rockefeller**",
    "I have not failed. I've just found 10,000 ways that won't work. — **Thomas A. Edison**",
    "The secret of getting ahead is getting started. — **Mark Twain**",
    "Your time is limited, don't waste it living someone else's life. — **Steve Jobs**",
    "Perfection is not attainable, but if we chase perfection we can catch excellence. — **Vince Lombardi**",
    "It always seems impossible until it's done. — **Nelson Mandela**",
    "A comfort zone is a beautiful place, but nothing ever grows there. — **Unknown**",
    "If you want to lift yourself up, lift up someone else. — **Booker T. Washington**",
    "The harder the conflict, the greater the triumph. — **George Washington**",
    "To handle yourself, use your head; to handle others, use your heart. — **Eleanor Roosevelt**",
    "Try not to become a man of success but rather try to become a man of value. — **Albert Einstein**",
    "The best revenge is massive success. — **Frank Sinatra**",
    "Your life does not get better by chance, it gets better by change. — **Jim Rohn**",
    "If opportunity doesn't knock, build a door. — **Milton Berle**",
    "Keep going. Be all in. — **Bryan Hutchinson**",
    "Don't limit your challenges. Challenge your limits. — **Unknown**",
    "Small deeds done are better than great deeds planned. — **Peter Marshall**",
    "Courage is grace under pressure. — **Ernest Hemingway**",
]


class QuoteCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="quote", description="Get a random inspirational quote.")
    async def quote(self, interaction: discord.Interaction):
        quote = random.choice(QUOTES)
        # Prefix the quote with the animated custom emoji (bot must have access to render it)
        emoji_prefix = "<a:quote:1424658219703205928> "
        await interaction.response.send_message(f"{emoji_prefix}{quote}", ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(QuoteCommand(bot))
