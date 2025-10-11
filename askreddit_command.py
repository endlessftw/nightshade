import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random


class AskRedditCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='askreddit', description='Get a random question from r/AskReddit')
    async def askreddit(self, interaction: discord.Interaction):
        # Defer the interaction since fetching from Reddit may take a moment
        await interaction.response.defer()

        try:
            # Fetch posts from r/AskReddit using Reddit's JSON API
            async with aiohttp.ClientSession() as session:
                # Get hot posts from AskReddit (top 100)
                url = 'https://www.reddit.com/r/AskReddit/hot.json?limit=100'
                headers = {'User-Agent': 'Discord Bot AskReddit Command 1.0'}
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        await interaction.followup.send('❌ Failed to fetch from r/AskReddit. Please try again later.', ephemeral=True)
                        return
                    
                    data = await response.json()
                    
                    # Extract posts
                    posts = data.get('data', {}).get('children', [])
                    
                    if not posts:
                        await interaction.followup.send('❌ No posts found on r/AskReddit.', ephemeral=True)
                        return
                    
                    # Filter to only include text posts (self posts) and exclude stickied posts
                    questions = []
                    for post in posts:
                        post_data = post.get('data', {})
                        # Skip stickied posts, videos, and non-self posts
                        if (not post_data.get('stickied', False) and 
                            post_data.get('is_self', False) and
                            not post_data.get('is_video', False)):
                            questions.append(post_data)
                    
                    if not questions:
                        await interaction.followup.send('❌ No questions found on r/AskReddit.', ephemeral=True)
                        return
                    
                    # Pick a random question
                    question = random.choice(questions)
                    
                    # Extract details
                    title = question.get('title', 'Unknown Question')
                    author = question.get('author', 'Unknown')
                    upvotes = question.get('ups', 0)
                    num_comments = question.get('num_comments', 0)
                    post_url = f"https://www.reddit.com{question.get('permalink', '')}"
                    
                    # Create embed
                    embed = discord.Embed(
                        title=title,
                        url=post_url,
                        color=discord.Color.orange(),
                        description=f"from r/AskReddit"
                    )
                    
                    # Add footer with stats
                    embed.set_footer(text=f"👤 u/{author} | ⬆️ {upvotes:,} upvotes | 💬 {num_comments:,} comments")
                    
                    # Add Reddit icon as thumbnail
                    embed.set_thumbnail(url="https://www.redditstatic.com/desktop2x/img/favicon/android-icon-192x192.png")
                    
                    await interaction.followup.send(embed=embed)
                    
        except aiohttp.ClientError as e:
            await interaction.followup.send(f'❌ Network error: {e}', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ An error occurred: {e}', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AskRedditCog(bot))
